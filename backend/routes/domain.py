# ============================================================
# routes/domain.py - GET /domain-check
# Analyzes a domain for fraud reputation signals
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.db_models import DomainReputation, BlacklistedEntity
from backend.models.schemas import DomainCheckResponse
from backend.ml.domain_check import DomainChecker

router = APIRouter()


@router.get("/domain-check", response_model=DomainCheckResponse, tags=["Domain"])
async def check_domain(
    domain: str = Query(..., description="Domain name to analyze (e.g. careers-jobs.xyz)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a domain name for fraud risk.
    Checks SSL, age, blacklists, naming patterns.
    Results are cached in database for 24 hours.
    """
    # Normalize domain input
    domain = domain.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]

    # --- Check database cache first ---
    cached = await db.execute(
        select(DomainReputation).where(DomainReputation.domain_name == domain)
    )
    cached_result = cached.scalar_one_or_none()

    # --- Load blacklisted domains ---
    bl_result = await db.execute(
        select(BlacklistedEntity.entity_value)
        .where(BlacklistedEntity.entity_type == "domain", BlacklistedEntity.active == True)
    )
    blacklisted_set = {row.entity_value for row in bl_result}

    # --- Run domain check ---
    checker = DomainChecker(blacklisted_domains=blacklisted_set)
    result = checker.check(domain)

    # Determine risk level from trust score
    if result.trust_score >= 0.7:
        risk_level = "LOW"
    elif result.trust_score >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # --- Cache result in DB ---
    if not cached_result:
        new_record = DomainReputation(
            domain_name=domain,
            ssl_valid=result.ssl_valid,
            trust_score=result.trust_score,
            blacklisted=result.blacklisted,
            suspicious_pattern=result.suspicious_pattern,
            report_count=0
        )
        db.add(new_record)
        await db.commit()

    return DomainCheckResponse(
        domain=domain,
        trust_score=round(result.trust_score, 3),
        risk_level=risk_level,
        domain_age_days=result.domain_age_days,
        ssl_valid=result.ssl_valid,
        blacklisted=result.blacklisted,
        suspicious_pattern=result.suspicious_pattern,
        whois_registrar=None,
        whois_country=None,
        report_count=cached_result.report_count if cached_result else 0,
        recommendation=result.recommendation
    )


# ============================================================
# routes/dashboard.py - GET /dashboard
# Analytics data for the admin dashboard
# ============================================================

from fastapi import APIRouter as DashRouter, Depends as DashDepends
from sqlalchemy.ext.asyncio import AsyncSession as DashSession
from sqlalchemy import text
from backend.database import get_db as dash_get_db
from backend.models.schemas import DashboardResponse, DashboardStats, TrendData

dash_router = DashRouter()


@dash_router.get("/dashboard", tags=["Dashboard"])
async def get_dashboard(db: DashSession = DashDepends(dash_get_db)):
    """
    Return aggregated analytics data for the admin dashboard.
    Used by the frontend dashboard.html page.
    """

    # --- Overall stats ---
    stats_result = await db.execute(text("""
        SELECT
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN is_flagged = TRUE THEN 1 END) as flagged_jobs,
            COUNT(CASE WHEN scam_score >= 61 THEN 1 END) as high_risk_jobs,
            COUNT(CASE WHEN scam_score >= 31 AND scam_score <= 60 THEN 1 END) as medium_risk_jobs,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as jobs_last_7_days
        FROM job_posts
    """))
    stats_row = stats_result.fetchone()

    report_result = await db.execute(text("""
        SELECT
            COUNT(*) as total_reports,
            COUNT(CASE WHEN reported_at >= NOW() - INTERVAL '7 days' THEN 1 END) as reports_last_7_days
        FROM scam_reports
    """))
    report_row = report_result.fetchone()

    recruiter_result = await db.execute(text("""
        SELECT
            COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified_count
        FROM recruiter_profiles
    """))
    recruiter_row = recruiter_result.fetchone()

    blacklist_result = await db.execute(text("""
        SELECT COUNT(*) as bl_count FROM domain_reputation WHERE blacklisted = TRUE
    """))
    bl_row = blacklist_result.fetchone()

    total_jobs = stats_row.total_jobs or 0
    high_risk = stats_row.high_risk_jobs or 0
    scam_pct = round((high_risk / total_jobs * 100) if total_jobs > 0 else 0, 1)

    stats = {
        "total_jobs_analyzed": total_jobs,
        "total_scam_reports": report_row.total_reports or 0,
        "high_risk_jobs": high_risk,
        "scam_percentage": scam_pct,
        "verified_recruiters": recruiter_row.verified_count or 0,
        "blacklisted_domains": bl_row.bl_count or 0,
        "jobs_last_7_days": stats_row.jobs_last_7_days or 0,
        "reports_last_7_days": report_row.reports_last_7_days or 0
    }

    # --- Monthly trends ---
    trend_result = await db.execute(text("""
        SELECT
            TO_CHAR(created_at, 'YYYY-MM') as period,
            COUNT(*) as total_count,
            COUNT(CASE WHEN scam_score >= 61 THEN 1 END) as scam_count
        FROM job_posts
        WHERE created_at >= NOW() - INTERVAL '6 months'
        GROUP BY period
        ORDER BY period ASC
    """))
    monthly_trends = [
        {
            "period": row.period,
            "total_count": row.total_count,
            "scam_count": row.scam_count,
            "scam_percentage": round((row.scam_count / row.total_count * 100)
                                     if row.total_count > 0 else 0, 1)
        }
        for row in trend_result.fetchall()
    ]

    # --- Top scam keywords ---
    keyword_result = await db.execute(text("""
        SELECT keyword, fraud_weight, category
        FROM flagged_keywords
        WHERE active = TRUE
        ORDER BY fraud_weight DESC
        LIMIT 10
    """))
    top_keywords = [
        {"keyword": row.keyword, "fraud_weight": row.fraud_weight, "category": row.category}
        for row in keyword_result.fetchall()
    ]

    # --- Top risk companies ---
    company_result = await db.execute(text("""
        SELECT company_name, AVG(scam_score) as avg_score, COUNT(*) as post_count
        FROM job_posts
        WHERE company_name IS NOT NULL AND scam_score >= 50
        GROUP BY company_name
        ORDER BY avg_score DESC
        LIMIT 10
    """))
    top_companies = [
        {"company": row.company_name, "avg_score": round(row.avg_score, 1), "count": row.post_count}
        for row in company_result.fetchall()
    ]

    # --- Recent high risk jobs ---
    recent_result = await db.execute(text("""
        SELECT job_id, title, company_name, scam_score, risk_level, created_at
        FROM job_posts
        WHERE scam_score >= 61
        ORDER BY created_at DESC
        LIMIT 10
    """))
    recent_high_risk = [
        {
            "job_id": str(row.job_id),
            "title": row.title,
            "company": row.company_name,
            "score": row.scam_score,
            "risk": row.risk_level,
            "date": row.created_at.isoformat() if row.created_at else None
        }
        for row in recent_result.fetchall()
    ]

    # --- Scam by type ---
    type_result = await db.execute(text("""
        SELECT scam_type, COUNT(*) as count
        FROM scam_reports
        GROUP BY scam_type
        ORDER BY count DESC
    """))
    scam_by_type = [
        {"type": row.scam_type, "count": row.count}
        for row in type_result.fetchall()
    ]

    return {
        "stats": stats,
        "monthly_trends": monthly_trends,
        "top_scam_keywords": top_keywords,
        "top_risk_companies": top_companies,
        "recent_high_risk_jobs": recent_high_risk,
        "scam_by_type": scam_by_type
    }


# ============================================================
# routes/blacklist.py - GET /blacklist
# Returns public blacklist of scam domains/companies/emails
# ============================================================

blacklist_router = DashRouter()


@blacklist_router.get("/blacklist", tags=["Blacklist"])
async def get_blacklist(
    entity_type: str = None,
    limit: int = 50,
    db: DashSession = DashDepends(dash_get_db)
):
    """
    Return active blacklist entries.
    Optionally filter by entity_type: domain / email / company / phone
    """
    from backend.models.db_models import BlacklistedEntity
    query = select(BlacklistedEntity).where(BlacklistedEntity.active == True)
    if entity_type:
        query = query.where(BlacklistedEntity.entity_type == entity_type)
    query = query.order_by(BlacklistedEntity.report_count.desc()).limit(min(limit, 200))

    result = await db.execute(query)
    entities = result.scalars().all()

    return [
        {
            "entity_type": e.entity_type,
            "entity_value": e.entity_value,
            "reason": e.reason,
            "severity": e.severity,
            "report_count": e.report_count
        }
        for e in entities
    ]
