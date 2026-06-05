# backend/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.database import get_db
from backend.auth import get_current_user, get_current_admin
import uuid
from datetime import datetime

router = APIRouter()

# Submit a scam report
@router.post("/reports")
async def submit_report(
    company_name: str,
    description: str,
    job_title: str = None,
    job_url: str = None,
    scam_type: str = "other",
    evidence_url: str = None,
    severity: int = 2,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new scam report"""
    from backend.models import ScamReport, UserActivity, BlacklistedEntity
    
    report = ScamReport(
        report_id=uuid.uuid4(),
        reported_by=current_user["user_id"],
        reporter_name=current_user.get("full_name"),
        company_name=company_name,
        job_title=job_title,
        job_url=job_url,
        description=description,
        evidence_url=evidence_url,
        scam_type=scam_type,
        severity=severity,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(report)
    
    # Log activity
    activity = UserActivity(
        activity_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        activity_type="scam_reported",
        details={
            "description": f"Reported scam from {company_name}",
            "icon": "🚨",
            "report_id": str(report.report_id)
        },
        created_at=datetime.utcnow()
    )
    db.add(activity)
    
    # Check if company should be auto-blacklisted (3+ reports)
    report_count = db.execute(
        select(func.count(ScamReport.report_id))
        .where(ScamReport.company_name.ilike(f"%{company_name}%"))
    ).scalar_one_or_none() or 0
    
    if report_count >= 2:  # After 2 reports, add to blacklist
        existing = db.execute(
            select(BlacklistedEntity)
            .where(
                BlacklistedEntity.entity_type == "company",
                BlacklistedEntity.entity_value.ilike(f"%{company_name}%")
            )
        ).scalar_one_or_none()
        
        if not existing:
            blacklist = BlacklistedEntity(
                entity_id=uuid.uuid4(),
                entity_type="company",
                entity_value=company_name,
                reason=f"Auto-blacklisted after {report_count + 1} user reports",
                severity="high",
                reported_by=current_user["user_id"],
                created_at=datetime.utcnow()
            )
            db.add(blacklist)
    
    db.commit()
    
    return {
        "report_id": str(report.report_id),
        "message": "Report submitted successfully",
        "status": "pending"
    }

# Get all reports (for community page)
@router.get("/reports")
async def get_reports(limit: int = 50, db: Session = Depends(get_db)):
    """Get all scam reports for community display"""
    from backend.models import ScamReport, User
    
    reports = db.execute(
        select(ScamReport, User.full_name, User.profile_image)
        .outerjoin(User, ScamReport.reported_by == User.user_id)
        .where(ScamReport.status != "rejected")
        .order_by(ScamReport.created_at.desc())
        .limit(limit)
    ).all()
    
    return [
        {
            "report_id": str(r.ScamReport.report_id),
            "company_name": r.ScamReport.company_name,
            "job_title": r.ScamReport.job_title,
            "description": r.ScamReport.description[:200],
            "scam_type": r.ScamReport.scam_type,
            "severity": r.ScamReport.severity,
            "status": r.ScamReport.status,
            "reporter_name": r.full_name or "Anonymous",
            "reporter_image": r.profile_image,
            "created_at": r.ScamReport.created_at.isoformat() if r.ScamReport.created_at else None
        }
        for r in reports
    ]

# Admin: Get pending reports
@router.get("/admin/reports/pending")
async def get_pending_reports(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to get pending reports"""
    from backend.models import ScamReport, User
    
    reports = db.execute(
        select(ScamReport, User.full_name, User.email)
        .outerjoin(User, ScamReport.reported_by == User.user_id)
        .where(ScamReport.status == "pending")
        .order_by(ScamReport.created_at.desc())
    ).all()
    
    return [
        {
            "report_id": str(r.ScamReport.report_id),
            "company_name": r.ScamReport.company_name,
            "job_title": r.ScamReport.job_title,
            "description": r.ScamReport.description,
            "scam_type": r.ScamReport.scam_type,
            "severity": r.ScamReport.severity,
            "evidence_url": r.ScamReport.evidence_url,
            "status": r.ScamReport.status,
            "reporter_name": r.full_name or "Anonymous",
            "reporter_email": r.email,
            "created_at": r.ScamReport.created_at.isoformat() if r.ScamReport.created_at else None
        }
        for r in reports
    ]

# Admin: Update report status
@router.put("/admin/reports/{report_id}")
async def update_report_status(
    report_id: str,
    status: str,
    admin_notes: str = None,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to update report status"""
    from backend.models import ScamReport
    
    report = db.execute(select(ScamReport).where(ScamReport.report_id == report_id)).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = status
    if admin_notes:
        report.admin_notes = admin_notes
    report.reviewed_at = datetime.utcnow()
    report.reviewed_by = admin["user_id"]
    
    db.commit()
    
    return {"message": "Report status updated"}

# Admin: Get all users
@router.get("/admin/users")
async def get_all_users(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """Admin endpoint to get all users"""
    from backend.models import User
    
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    
    return [
        {
            "user_id": str(u.user_id),
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "profile_image": u.profile_image,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

# Admin: Update user role
@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to update user role"""
    from backend.models import User
    
    user = db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User role updated"}

# Admin: Add to blacklist
@router.post("/admin/blacklist")
async def add_to_blacklist(
    entity_type: str,
    entity_value: str,
    reason: str = None,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to add entity to blacklist"""
    from backend.models import BlacklistedEntity
    
    existing = db.execute(
        select(BlacklistedEntity)
        .where(
            BlacklistedEntity.entity_type == entity_type,
            BlacklistedEntity.entity_value == entity_value
        )
    ).scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Entity already blacklisted")
    
    blacklist = BlacklistedEntity(
        entity_id=uuid.uuid4(),
        entity_type=entity_type,
        entity_value=entity_value,
        reason=reason,
        severity="high",
        reported_by=admin["user_id"],
        created_at=datetime.utcnow()
    )
    db.add(blacklist)
    db.commit()
    
    return {"message": "Entity added to blacklist"}

# Admin: Get blacklist
@router.get("/admin/blacklist")
async def get_blacklist(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to get blacklist"""
    from backend.models import BlacklistedEntity
    
    items = db.execute(select(BlacklistedEntity).order_by(BlacklistedEntity.created_at.desc())).scalars().all()
    
    return [
        {
            "entity_id": str(i.entity_id),
            "entity_type": i.entity_type,
            "entity_value": i.entity_value,
            "reason": i.reason,
            "severity": i.severity,
            "created_at": i.created_at.isoformat() if i.created_at else None
        }
        for i in items
    ]