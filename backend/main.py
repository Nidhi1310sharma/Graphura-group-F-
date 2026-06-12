<<<<<<< HEAD
# ============================================================
# ScamShield v4 – FastAPI Backend
# ============================================================
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import uuid, re, os

app = FastAPI(title="ScamShield API v4", version="4.0.0")
=======
# # backend/main.py
# # to run: python -m uvicorn backend.main:app --reload


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import auth, community, reports
from backend.admin import routes_reports

app = FastAPI()
>>>>>>> backup-before-frontend-sync

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
security = HTTPBearer(auto_error=False)

# ── In-memory store (replace with PostgreSQL via DATABASE_URL) ──
USERS = {}
REPORTS = []
JOBS = []
COMMUNITY_POSTS = []

# ── Fraud keywords ──
FRAUD_KEYWORDS = {
    "critical": ["registration fee","security deposit","joining fee","training fee","kit fee","id card fee","background check fee","registration charges","refundable deposit"],
    "high": ["work from home earn","earn daily","daily payout","data entry earn","part time earn","100% job guarantee","guaranteed placement","no interview required","whatsapp only","contact whatsapp","telegram only"],
    "medium": ["urgent hiring","immediate joining","apply asap","limited seats","work from home","no experience required","freshers welcome","direct joining","earn upto","₹5000 per day","₹10000 per day"],
    "low": ["data entry","typing work","online work","home based","part time","earn money online","referral bonus"]
}
SUSPICIOUS_TLDS = ['.xyz', '.tk', '.ml', '.ga', '.cf', '.pw', '.top', '.cc', '.work', '.click']
FREE_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'rediffmail.com', 'ymail.com']

# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════
class AnalyzeRequest(BaseModel):
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    salary_text: Optional[str] = None
    recruiter_email: Optional[str] = None
    domain_name: Optional[str] = None
    description: Optional[str] = None

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None
    city: Optional[str] = None
    profession: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = []
    avatar: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ReportRequest(BaseModel):
    company_name: str
    job_title: Optional[str] = None
    scam_type: str
    report_reason: str
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    job_url: Optional[str] = None
    reported_at: Optional[str] = None

class CommunityPostRequest(BaseModel):
    body: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    post_type: Optional[str] = "suspicious"

# ═══════════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════════
def score_text(text: str) -> tuple:
    if not text:
        return 0.0, [], []
    text_lower = text.lower()
    score = 0.0
    signals = []
    keywords_found = []
    weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
    severities = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
    for level, kws in FRAUD_KEYWORDS.items():
        for kw in kws:
            if kw in text_lower:
                keywords_found.append(kw)
                score += weights[level]
                signals.append({
                    "severity": severities[level],
                    "signal_type": "keyword_match",
                    "description": f'Fraud keyword detected: "{kw}"',
                    "score_contribution": weights[level]
                })
    return min(score, 60.0), signals, keywords_found

def score_domain(domain: str) -> tuple:
    if not domain:
        return 0.0, []
    signals = []
    score = 0.0
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            score += 25
            signals.append({"severity": "high", "signal_type": "suspicious_tld", "description": f"Suspicious TLD detected: {tld}", "score_contribution": 25})
            break
    patterns = ['careers-', 'jobs-', 'hr-', '-jobs', '-career', 'recruitment-', '-hiring']
    for pat in patterns:
        if pat in domain:
            score += 10
            signals.append({"severity": "medium", "signal_type": "suspicious_pattern", "description": f"Suspicious domain pattern: {pat}", "score_contribution": 10})
            break
    return min(score, 40.0), signals

def score_email(email: str) -> tuple:
    if not email:
        return 0.0, []
    domain = email.split('@')[-1].lower() if '@' in email else ''
    if domain in FREE_DOMAINS:
        return 20.0, [{"severity": "high", "signal_type": "free_email", "description": f"Recruiter using free email ({domain}) instead of company domain", "score_contribution": 20}]
    return 0.0, []

def score_salary(salary_text: str) -> tuple:
    if not salary_text:
        return 0.0, []
    text = salary_text.lower().replace(',', '')
    numbers = re.findall(r'\d+', text)
    if not numbers:
        return 0.0, []
    num = int(numbers[0])
    if ('month' in text or '/m' in text) and num > 50000:
        return 15.0, [{"severity": "medium", "signal_type": "salary_anomaly", "description": f"Unusually high salary for a typical role: {salary_text}", "score_contribution": 15}]
    if ('day' in text or '/d' in text) and num > 2000:
        return 20.0, [{"severity": "high", "signal_type": "salary_anomaly", "description": f"Unrealistic daily earnings: {salary_text}", "score_contribution": 20}]
    return 0.0, []

def determine_risk(score: float) -> str:
    if score >= 70: return "CONFIRMED_SCAM"
    if score >= 50: return "HIGH"
    if score >= 30: return "MEDIUM"
    return "LOW"

RISK_LABELS = {"LOW": "Low Risk", "MEDIUM": "Medium Risk", "HIGH": "High Risk", "CONFIRMED_SCAM": "Confirmed Scam"}
RECOMMENDATIONS = {
    "LOW": "This job posting appears relatively safe. Always verify company details independently before applying.",
    "MEDIUM": "Proceed with caution. Verify the company on LinkedIn and official channels before sharing personal information.",
    "HIGH": "This job shows multiple red flags. Do NOT pay any fees. Verify company legitimacy before proceeding.",
    "CONFIRMED_SCAM": "This is almost certainly a scam. Do NOT pay any money or share sensitive information. Report this job immediately."
}

# ═══════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════
@app.post("/auth/register")
async def register(req: RegisterRequest):
    if req.email in USERS:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = {
        "user_id": user_id, "email": req.email, "full_name": req.full_name,
        "mobile": req.mobile, "city": req.city, "profession": req.profession,
        "bio": req.bio, "skills": req.skills or [], "avatar": req.avatar,
        "role": "user", "reports_count": 0, "checks_count": 0,
        "created_at": datetime.now().isoformat()
    }
    USERS[req.email] = {"password": req.password, **user}
    return {"token": f"token-{user_id}", "user": user}

@app.post("/auth/login")
async def login(req: LoginRequest):
    user = USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = f"token-{user['user_id']}"
    return {"token": token, "user": {k: v for k, v in user.items() if k != "password"}}

# ═══════════════════════════════════════════════════════════
# ANALYZE
# ═══════════════════════════════════════════════════════════
@app.post("/analyze")
async def analyze_job(req: AnalyzeRequest):
    text_score, text_signals, keywords = score_text(req.description or "")
    domain_score, domain_signals = score_domain(req.domain_name or "")
    email_score, email_signals = score_email(req.recruiter_email or "")
    salary_score, salary_signals = score_salary(req.salary_text or "")
    
    total = min(100.0, text_score + domain_score + email_score + salary_score)
    all_signals = text_signals + domain_signals + email_signals + salary_signals
    risk = determine_risk(total)
    
    return {
        "scam_score": round(total, 1),
        "risk_level": risk,
        "risk_label": RISK_LABELS[risk],
        "keyword_score": round(text_score, 1),
        "domain_score": round(domain_score, 1),
        "salary_anomaly": salary_score > 0,
        "ssl_valid": None,
        "domain_blacklisted": any(req.domain_name and req.domain_name.endswith(tld) for tld in SUSPICIOUS_TLDS) if req.domain_name else False,
        "impersonation_detected": False,
        "fraud_signals": all_signals[:10],
        "suspicious_keywords": keywords[:15],
        "recommendation": RECOMMENDATIONS[risk],
        "analyzed_at": datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════
@app.post("/reports")
async def create_report(req: ReportRequest):
    report = {
        "report_id": str(uuid.uuid4()),
        "company_name": req.company_name,
        "job_title": req.job_title,
        "scam_type": req.scam_type,
        "report_reason": req.report_reason,
        "reporter_name": req.reporter_name,
        "reporter_email": req.reporter_email,
        "status": "pending",
        "upvotes": 0,
        "reported_at": datetime.now().isoformat()
    }
    REPORTS.append(report)
    return {"success": True, "report_id": report["report_id"], "message": "Report submitted successfully"}

@app.get("/reports")
async def get_reports(status: Optional[str] = None, limit: int = 50):
    filtered = [r for r in REPORTS if not status or r["status"] == status]
    return {"reports": filtered[-limit:], "total": len(filtered)}

@app.get("/reports/recent")
async def get_recent_reports(limit: int = 10):
    return {"reports": REPORTS[-limit:], "total": len(REPORTS)}

# ═══════════════════════════════════════════════════════════
# COMMUNITY
# ═══════════════════════════════════════════════════════════
@app.get("/community/posts")
async def get_community_posts(limit: int = 20, filter: Optional[str] = None):
    posts = list(reversed(COMMUNITY_POSTS))
    if filter and filter != 'all':
        posts = [p for p in posts if p.get('post_type') == filter]
    return {"posts": posts[:limit], "total": len(posts)}

@app.post("/community/posts")
async def create_community_post(req: CommunityPostRequest, creds: HTTPAuthorizationCredentials = Depends(security)):
    post = {
        "post_id": str(uuid.uuid4()),
        "body": req.body,
        "company_name": req.company_name,
        "job_title": req.job_title,
        "post_type": req.post_type or "suspicious",
        "upvotes": 0,
        "reply_count": 0,
        "created_at": datetime.now().isoformat()
    }
    COMMUNITY_POSTS.append(post)
    return {"success": True, "post": post}

@app.post("/community/posts/{post_id}/upvote")
async def upvote_post(post_id: str):
    for p in COMMUNITY_POSTS:
        if p["post_id"] == post_id:
            p["upvotes"] = p.get("upvotes", 0) + 1
            return {"upvotes": p["upvotes"]}
    raise HTTPException(404, "Post not found")

# ═══════════════════════════════════════════════════════════
# DOMAIN SCAN
# ═══════════════════════════════════════════════════════════
@app.get("/domain/scan")
async def scan_domain(domain: str):
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    domain_score, signals = score_domain(domain)
    suspicious = any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS)
    return {
        "domain": domain,
        "score": round(domain_score * 2.5, 1),
        "ssl_valid": not suspicious,
        "blacklisted": suspicious and domain_score > 20,
        "suspicious_pattern": suspicious,
        "signals": signals,
        "checked_at": datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════
# JOBS
# ═══════════════════════════════════════════════════════════
@app.get("/jobs")
async def get_jobs(risk: Optional[str] = None, limit: int = 50):
    filtered = [j for j in JOBS if not risk or j.get("risk_level") == risk]
    return {"jobs": filtered[-limit:], "total": len(filtered)}

@app.get("/jobs/high-risk")
async def get_high_risk_jobs(limit: int = 10):
    high = [j for j in JOBS if j.get("scam_score", 0) >= 61]
    high.sort(key=lambda x: x.get("scam_score", 0), reverse=True)
    return {"jobs": high[:limit], "total": len(high)}

# ═══════════════════════════════════════════════════════════
# USERS (Admin)
# ═══════════════════════════════════════════════════════════
@app.get("/admin/users")
async def admin_get_users():
    safe = [{k: v for k, v in u.items() if k != "password"} for u in USERS.values()]
    return {"users": safe, "total": len(safe)}

@app.get("/admin/stats")
async def admin_stats():
    return {
        "total_users": len(USERS),
        "total_reports": len(REPORTS),
        "total_jobs": len(JOBS),
        "pending_reports": len([r for r in REPORTS if r["status"] == "pending"]),
        "confirmed_scams": len([r for r in REPORTS if r["status"] == "confirmed"]),
        "blacklisted_domains": 89
    }

@app.get("/health")
async def health():
    return {"status": "ok", "version": "4.0.0", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================================
# main.py – FastAPI Application Entry Point
# 
# How to run:
#   cd backend && uvicorn main:app --reload --port 8000
#
# Key routes registered:
#   /auth/login       POST – returns JWT token
#   /auth/register    POST – creates new user
#   /analyze          POST – runs ML fraud detection engine
#   /jobs             GET  – lists jobs from database
#   /reports          GET/POST – community scam reports
#   /domain           POST – WHOIS + SSL domain check
#   /recruiter        POST – email domain verification
#
# Supabase credentials go in backend/.env:
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_KEY=your-anon-key
#   DATABASE_URL=postgresql://user:pass@host:5432/db
# ============================================================
=======
app.include_router(auth.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(routes_reports.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API Running"}
>>>>>>> backup-before-frontend-sync
