# ============================================================
# routes/analyze.py - POST /analyze
# Main endpoint: analyze a job posting for scam signals
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
import uuid

from backend.database import get_db
from backend.models.db_models import JobPost, FlaggedKeyword, BlacklistedEntity, ScamReport, AnalyticsEvent
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, FraudSignal
from backend.ml.fraud_engine import FraudEngine

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_job(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    Analyze a job posting for fraud signals.
    
    Accepts job URL, description, salary, domain, or recruiter email.
    Returns a scam probability score with detailed fraud signals.
    """

    # --- Load custom keywords from database ---
    kw_result = await db.execute(
        select(FlaggedKeyword.keyword, FlaggedKeyword.fraud_weight)
        .where(FlaggedKeyword.active == True)
    )
    custom_keywords = {row.keyword: row.fraud_weight for row in kw_result}

    # --- Load blacklisted domains from database ---
    bl_result = await db.execute(
        select(BlacklistedEntity.entity_value)
        .where(BlacklistedEntity.entity_type == "domain", BlacklistedEntity.active == True)
    )
    blacklisted_domains = {row.entity_value for row in bl_result}

    # --- Check user report count for this domain/company ---
    user_report_count = 0
    if request.company_name:
        count_result = await db.execute(
            select(func.count(ScamReport.report_id))
            .where(ScamReport.company_name.ilike(f"%{request.company_name}%"))
        )
        user_report_count = count_result.scalar() or 0

    # --- Run Fraud Engine ---
    engine = FraudEngine(
        blacklisted_domains=blacklisted_domains,
        custom_keywords=custom_keywords
    )

    result = engine.analyze(
        description=request.description or "",
        title=request.job_title or "",
        company_name=request.company_name or "",
        domain=request.domain_name or _extract_domain(request.job_url),
        salary_text=request.salary_text or "",
        recruiter_email=request.recruiter_email or "",
        user_report_count=user_report_count
    )

    # --- Save analyzed job to database ---
    job_post = JobPost(
        job_id=uuid.uuid4(),
        title=request.job_title or "Untitled",
        company_name=request.company_name,
        salary_text=request.salary_text,
        location=request.location,
        description=request.description,
        source_url=request.job_url,
        domain_name=request.domain_name or _extract_domain(request.job_url),
        recruiter_email=request.recruiter_email,
        source_platform="user_submitted",
        scam_score=result.scam_score,
        risk_level=result.risk_level,
        is_flagged=result.scam_score >= 60,
        keyword_score=result.keyword_score,
        domain_score=result.domain_score,
        salary_score=result.salary_score,
        grammar_score=0.0,
        analyzed_at=datetime.now(timezone.utc)
    )
    db.add(job_post)

    # --- Log analytics event (no PII) ---
    event = AnalyticsEvent(
        event_type="scan",
        scam_score=result.scam_score,
        risk_level=result.risk_level,
        platform=_extract_domain(request.job_url) if request.job_url else "direct"
    )
    db.add(event)

    await db.commit()

    # --- Build fraud signal objects ---
    fraud_signals = [
        FraudSignal(
            signal_type=s.get("signal_type", "unknown"),
            description=s.get("description", ""),
            severity=s.get("severity", "medium"),
            score_contribution=s.get("score_contribution", 0)
        )
        for s in result.fraud_signals
    ]

    return AnalyzeResponse(
        job_id=job_post.job_id,
        scam_score=result.scam_score,
        risk_level=result.risk_level,
        risk_label=result.risk_label,
        risk_color=result.risk_color,
        keyword_score=result.keyword_score,
        domain_score=result.domain_score,
        salary_score=result.salary_score,
        suspicious_keywords=result.suspicious_keywords,
        fraud_signals=fraud_signals,
        domain_age_days=result.domain_age_days,
        ssl_valid=result.ssl_valid,
        domain_blacklisted=result.domain_blacklisted,
        salary_anomaly=result.salary_anomaly,
        recommendation=result.recommendation,
        analyzed_at=datetime.now(timezone.utc).isoformat()
    )


def _extract_domain(url: str) -> str:
    """Extract domain from a URL string."""
    if not url:
        return ""
    url = url.strip().lower()
    url = url.replace("https://", "").replace("http://", "")
    url = url.split("/")[0]
    return url
