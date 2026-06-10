# ============================================================
# routes/recruiter.py - GET /recruiter-check
# Verify a recruiter by email or company domain
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models.db_models import RecruiterProfile, BlacklistedEntity, ScamReport
from backend.models.schemas import RecruiterCheckResponse
from backend.ml.domain_check import DomainChecker

router = APIRouter()

# Personal email domains that companies should NOT use for HR
PERSONAL_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "rediffmail.com", "yahoo.in", "ymail.com"
]


@router.get("/recruiter-check", response_model=RecruiterCheckResponse, tags=["Recruiter"])
async def check_recruiter(
    email: str = Query(None, description="Recruiter email address"),
    domain: str = Query(None, description="Company domain name"),
    company: str = Query(None, description="Company name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a recruiter's legitimacy using email, domain, or company name.
    Returns trust score and blacklist status.
    """

    blacklisted = False
    blacklist_reason = None
    previous_reports = 0
    trust_score = 70.0

    # --- Check blacklist for email ---
    if email:
        bl_result = await db.execute(
            select(BlacklistedEntity)
            .where(
                BlacklistedEntity.entity_type == "email",
                BlacklistedEntity.entity_value == email.lower(),
                BlacklistedEntity.active == True
            )
        )
        bl_entity = bl_result.scalar_one_or_none()
        if bl_entity:
            blacklisted = True
            blacklist_reason = bl_entity.reason
            trust_score = 5.0

    # --- Check blacklist for company ---
    if company and not blacklisted:
        bl_result = await db.execute(
            select(BlacklistedEntity)
            .where(
                BlacklistedEntity.entity_type == "company",
                BlacklistedEntity.entity_value.ilike(f"%{company}%"),
                BlacklistedEntity.active == True
            )
        )
        bl_entity = bl_result.scalar_one_or_none()
        if bl_entity:
            blacklisted = True
            blacklist_reason = bl_entity.reason
            trust_score = 10.0

    # --- Check report count ---
    if company:
        report_result = await db.execute(
            select(func.count(ScamReport.report_id))
            .where(ScamReport.company_name.ilike(f"%{company}%"))
        )
        previous_reports = report_result.scalar() or 0
        trust_score -= min(previous_reports * 10, 40)

    # --- Penalize personal email usage ---
    ssl_valid = None
    domain_verified = None
    if email:
        email_domain = email.split("@")[-1].lower()
        if email_domain in PERSONAL_EMAIL_DOMAINS:
            trust_score -= 20

    # --- Domain check ---
    if domain:
        checker = DomainChecker()
        domain_result = checker.check(domain)
        trust_score = min(trust_score, domain_result.trust_score * 100)
        ssl_valid = domain_result.ssl_valid
        domain_verified = not domain_result.suspicious_pattern

    # Clamp trust score
    trust_score = max(0.0, min(100.0, trust_score))

    # Determine status
    if blacklisted:
        status = "BLACKLISTED"
        recommendation = "⛔ This recruiter/company is blacklisted. Do NOT share personal details."
    elif trust_score < 30:
        status = "SUSPICIOUS"
        recommendation = "⚠️ Multiple red flags detected. Research this recruiter thoroughly before responding."
    elif trust_score < 60:
        status = "SUSPICIOUS"
        recommendation = "⚠️ Some concerns found. Verify through LinkedIn or official company website."
    else:
        status = "UNKNOWN"
        recommendation = "ℹ️ No records found. Always verify recruiter identity through official company channels."

    return RecruiterCheckResponse(
        email=email,
        domain=domain,
        company=company,
        status=status,
        trust_score=round(trust_score, 1),
        previous_reports=previous_reports,
        blacklisted=blacklisted,
        blacklist_reason=blacklist_reason,
        domain_verified=domain_verified,
        ssl_valid=ssl_valid,
        recommendation=recommendation
    )
