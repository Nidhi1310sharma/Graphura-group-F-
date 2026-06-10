# ============================================================
# routes/report.py - POST /report
# Handles user-submitted scam reports
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime, timezone
import uuid

from backend.database import get_db
from backend.models.db_models import ScamReport, BlacklistedEntity, AnalyticsEvent
from backend.models.schemas import ReportRequest, ReportResponse

router = APIRouter()


@router.post("/report", response_model=ReportResponse, tags=["Reports"])
async def submit_report(request: ReportRequest, db: AsyncSession = Depends(get_db)):
    """
    Submit a scam report for a suspicious job posting.
    Automatically escalates severity if the same domain/company
    has been reported multiple times.
    """

    # Create the report record
    report = ScamReport(
        report_id=uuid.uuid4(),
        company_name=request.company_name,
        job_title=request.job_title,
        job_url=request.job_url,
        scam_type=request.scam_type,
        report_reason=request.report_reason,
        user_comment=request.user_comment,
        severity=request.severity,
        screenshot_url=request.screenshot_url,
        reporter_email=request.reporter_email,
        reporter_name=request.reporter_name,
        status="pending",
        reported_at=datetime.now(timezone.utc)
    )
    db.add(report)

    # --- Auto-blacklist if multiple reports for same company ---
    existing_reports = await db.execute(
        select(func.count(ScamReport.report_id))
        .where(ScamReport.company_name.ilike(f"%{request.company_name}%"))
    )
    report_count = (existing_reports.scalar() or 0) + 1

    if report_count >= 3:
        # Auto-add to blacklist
        existing_bl = await db.execute(
            select(BlacklistedEntity)
            .where(
                BlacklistedEntity.entity_type == "company",
                BlacklistedEntity.entity_value.ilike(f"%{request.company_name}%")
            )
        )
        if not existing_bl.scalar_one_or_none():
            bl_entry = BlacklistedEntity(
                entity_type="company",
                entity_value=request.company_name,
                reason=f"Auto-blacklisted after {report_count} user reports",
                report_count=report_count,
                severity="high",
                source="auto_detected"
            )
            db.add(bl_entry)

    # Log analytics event
    event = AnalyticsEvent(event_type="report")
    db.add(event)

    await db.commit()

    return ReportResponse(
        report_id=report.report_id,
        status="pending",
        message="Thank you! Your report has been submitted and will be reviewed by our team.",
        reported_at=report.reported_at.isoformat()
    )


@router.get("/reports", tags=["Reports"])
async def get_recent_reports(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get recent scam reports (public endpoint - no PII)."""
    result = await db.execute(
        select(
            ScamReport.report_id,
            ScamReport.company_name,
            ScamReport.job_title,
            ScamReport.scam_type,
            ScamReport.severity,
            ScamReport.status,
            ScamReport.reported_at
        )
        .order_by(ScamReport.reported_at.desc())
        .limit(min(limit, 100))
    )
    rows = result.fetchall()
    return [
        {
            "report_id": str(row.report_id),
            "company_name": row.company_name,
            "job_title": row.job_title,
            "scam_type": row.scam_type,
            "severity": row.severity,
            "status": row.status,
            "reported_at": row.reported_at.isoformat() if row.reported_at else None
        }
        for row in rows
    ]
