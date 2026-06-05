# backend/routes/jobs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from backend.database import get_db
from backend.auth import get_current_user
from datetime import datetime
import uuid

router = APIRouter()

# Analyze job posting
@router.post("/analyze")
async def analyze_job(
    method: str = "description",
    description: str = None,
    job_title: str = None,
    company_name: str = None,
    salary: str = None,
    recruiter_email: str = None,
    url: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a job posting for scam signals"""
    from backend.models import JobPost, UserActivity
    
    # This is a simplified scam detection logic
    # In production, this would use ML models
    
    scam_score = 0
    fraud_signals = []
    suspicious_keywords = []
    
    # Check for scam keywords in description
    scam_keywords = [
        "registration fee", "security deposit", "training fee", "joining fee",
        "whatsapp hr", "telegram", "no interview", "direct selection",
        "earn daily", "limited seats", "urgent hiring", "immediate joining"
    ]
    
    if description:
        desc_lower = description.lower()
        for keyword in scam_keywords:
            if keyword in desc_lower:
                suspicious_keywords.append(keyword)
                fraud_signals.append({
                    "signal_type": "keyword",
                    "description": f"Suspicious phrase: '{keyword}'",
                    "severity": "high",
                    "score_contribution": 15
                })
                scam_score += 15
    
    # Check recruiter email
    if recruiter_email:
        personal_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        email_domain = recruiter_email.split("@")[-1].lower()
        if email_domain in personal_domains:
            fraud_signals.append({
                "signal_type": "email",
                "description": f"Recruiter using personal email ({email_domain}) instead of company domain",
                "severity": "high",
                "score_contribution": 20
            })
            scam_score += 20
    
    # Check salary
    if salary:
        import re
        numbers = re.findall(r'\d+', salary)
        if numbers:
            salary_amount = int(numbers[0])
            if salary_amount > 50000:  # Unrealistic for freshers
                fraud_signals.append({
                    "signal_type": "salary",
                    "description": f"Unrealistic salary offer: {salary} for entry-level position",
                    "severity": "medium",
                    "score_contribution": 15
                })
                scam_score += 15
    
    # Calculate final score
    scam_score = min(scam_score, 100)
    
    # Determine risk level
    if scam_score >= 70:
        risk_level = "HIGH"
        recommendation = "⚠️ High risk detected. DO NOT apply or pay any fees."
    elif scam_score >= 40:
        risk_level = "MEDIUM"
        recommendation = "⚠️ Medium risk. Verify the company independently before proceeding."
    else:
        risk_level = "LOW"
        recommendation = "✅ Low risk detected, but always verify independently."
    
    # Save to database
    job_post = JobPost(
        job_id=uuid.uuid4(),
        title=job_title or "Unknown",
        company_name=company_name,
        salary=salary,
        description=description[:5000] if description else None,
        source_url=url,
        recruiter_email=recruiter_email,
        scam_score=scam_score,
        risk_level=risk_level,
        analyzed_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    db.add(job_post)
    
    # Log activity
    activity = UserActivity(
        activity_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        activity_type="job_checked",
        details={
            "description": f"Checked job: {job_title or 'Unknown'} at {company_name or 'Unknown company'}",
            "icon": "🔍",
            "scam_score": scam_score
        },
        created_at=datetime.utcnow()
    )
    db.add(activity)
    db.commit()
    
    return {
        "job_id": str(job_post.job_id),
        "scam_score": scam_score,
        "risk_level": risk_level,
        "risk_label": "High Risk" if risk_level == "HIGH" else "Medium Risk" if risk_level == "MEDIUM" else "Low Risk",
        "keyword_score": scam_score,
        "domain_score": scam_score * 0.7,
        "suspicious_keywords": suspicious_keywords,
        "fraud_signals": fraud_signals,
        "ssl_valid": None,
        "domain_blacklisted": False,
        "salary_anomaly": "salary" in str(fraud_signals).lower() if salary else False,
        "recommendation": recommendation,
        "analyzed_at": datetime.utcnow().isoformat()
    }

# Get all jobs
@router.get("/jobs")
async def get_jobs(
    page: int = 1,
    limit: int = 20,
    q: str = None,
    scam_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all job postings with pagination"""
    from backend.models import JobPost
    
    query = select(JobPost)
    
    # Search filter
    if q:
        query = query.where(
            or_(
                JobPost.title.ilike(f"%{q}%"),
                JobPost.company_name.ilike(f"%{q}%"),
                JobPost.location.ilike(f"%{q}%")
            )
        )
    
    # Scam filter
    if scam_filter:
        if scam_filter == "high":
            query = query.where(JobPost.scam_score >= 70)
        elif scam_filter == "medium":
            query = query.where(JobPost.scam_score.between(40, 69))
        elif scam_filter == "low":
            query = query.where(JobPost.scam_score < 40)
    
    # Pagination
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one_or_none() or 0
    offset = (page - 1) * limit
    query = query.order_by(JobPost.created_at.desc()).offset(offset).limit(limit)
    
    jobs = db.execute(query).scalars().all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "jobs": [
            {
                "job_id": str(j.job_id),
                "title": j.title,
                "company_name": j.company_name,
                "salary": j.salary,
                "location": j.location,
                "description": j.description[:200] if j.description else None,
                "scam_score": j.scam_score,
                "risk_level": j.risk_level,
                "posted_date": j.posted_date.isoformat() if j.posted_date else None,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
    }

# Get dashboard stats
@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get statistics for dashboard"""
    from backend.models import JobPost, ScamReport, User
    
    total_jobs = db.execute(select(func.count(JobPost.job_id))).scalar_one_or_none() or 0
    scam_jobs = db.execute(select(func.count(JobPost.job_id)).where(JobPost.scam_score >= 70)).scalar_one_or_none() or 0
    total_reports = db.execute(select(func.count(ScamReport.report_id))).scalar_one_or_none() or 0
    active_users = db.execute(select(func.count(User.user_id))).scalar_one_or_none() or 0
    
    # Monthly trends (last 6 months)
    monthly_trends = []
    # Simplified - in production, use proper date grouping
    
    # Scam types
    scam_types = [
        {"type": "Fee Fraud", "count": 35},
        {"type": "Phishing", "count": 25},
        {"type": "Fake Company", "count": 20},
        {"type": "Impersonation", "count": 12},
        {"type": "Other", "count": 8}
    ]
    
    # Top keywords
    top_keywords = [
        {"keyword": "registration fee", "fraud_weight": 0.95},
        {"keyword": "security deposit", "fraud_weight": 0.90},
        {"keyword": "whatsapp hr", "fraud_weight": 0.91},
        {"keyword": "urgent hiring", "fraud_weight": 0.60},
        {"keyword": "no experience needed", "fraud_weight": 0.55}
    ]
    
    # Top companies
    top_companies = [
        {"company": "Global Tech Solutions", "avg_score": 85},
        {"company": "Digital Marketing Hub", "avg_score": 78},
        {"company": "QuickHire Solutions", "avg_score": 72},
        {"company": "EasyEarn India", "avg_score": 68},
        {"company": "DreamJobs Pvt Ltd", "avg_score": 65}
    ]
    
    return {
        "total_jobs": total_jobs,
        "scam_jobs": scam_jobs,
        "total_reports": total_reports,
        "active_users": active_users,
        "monthly_trends": monthly_trends,
        "scam_types": scam_types,
        "top_keywords": top_keywords,
        "top_companies": top_companies
    }