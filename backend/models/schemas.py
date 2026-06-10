# ============================================================
# models/schemas.py - Pydantic Schemas
# Define request bodies and response shapes for API endpoints
# ============================================================

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ---------------------------------------------------------------
# Analyze Endpoint Schemas
# ---------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze
    User can submit a job URL, paste the description, or both.
    """
    job_url: Optional[str] = None           # URL of the job posting
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    description: Optional[str] = None       # Paste job description text
    salary_text: Optional[str] = None       # e.g. "₹80,000/month"
    recruiter_email: Optional[str] = None
    domain_name: Optional[str] = None       # e.g. "example.xyz"
    location: Optional[str] = None

    @field_validator("job_url", "domain_name")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if v else v


class FraudSignal(BaseModel):
    """A single fraud signal detected during analysis."""
    signal_type: str                        # keyword / domain / salary / grammar
    description: str
    severity: str                           # low / medium / high
    score_contribution: float


class AnalyzeResponse(BaseModel):
    """Response from POST /analyze"""
    job_id: Optional[UUID] = None
    scam_score: float                       # 0-100
    risk_level: str                         # LOW / MEDIUM / HIGH / CONFIRMED_SCAM
    risk_label: str                         # Human readable: "Low Risk", etc.
    risk_color: str                         # CSS color: green / orange / red
    keyword_score: float
    domain_score: float
    salary_score: float
    suspicious_keywords: List[str]
    fraud_signals: List[FraudSignal]
    domain_age_days: Optional[int] = None
    ssl_valid: Optional[bool] = None
    domain_blacklisted: bool = False
    salary_anomaly: bool = False
    recommendation: str
    analyzed_at: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------
# Report Endpoint Schemas
# ---------------------------------------------------------------

class ReportRequest(BaseModel):
    """Request body for POST /report"""
    company_name: str
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    scam_type: str                          # fee_demand / phishing / fake_company / data_theft / other
    report_reason: str
    user_comment: Optional[str] = None
    severity: int = 2                       # 1=low, 2=medium, 3=high, 4=critical
    screenshot_url: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_name: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError("Severity must be 1, 2, 3, or 4")
        return v


class ReportResponse(BaseModel):
    """Response from POST /report"""
    report_id: UUID
    status: str
    message: str
    reported_at: str


# ---------------------------------------------------------------
# Recruiter Check Schemas
# ---------------------------------------------------------------

class RecruiterCheckResponse(BaseModel):
    """Response from GET /recruiter-check"""
    email: Optional[str] = None
    domain: Optional[str] = None
    company: Optional[str] = None
    status: str                             # VERIFIED / SUSPICIOUS / BLACKLISTED / UNKNOWN
    trust_score: float                      # 0-100
    previous_reports: int
    blacklisted: bool
    blacklist_reason: Optional[str] = None
    domain_verified: Optional[bool] = None
    ssl_valid: Optional[bool] = None
    recommendation: str


# ---------------------------------------------------------------
# Domain Check Schemas
# ---------------------------------------------------------------

class DomainCheckResponse(BaseModel):
    """Response from GET /domain-check"""
    domain: str
    trust_score: float                      # 0-1
    risk_level: str
    domain_age_days: Optional[int] = None
    ssl_valid: Optional[bool] = None
    blacklisted: bool
    suspicious_pattern: bool
    whois_registrar: Optional[str] = None
    whois_country: Optional[str] = None
    report_count: int
    recommendation: str


# ---------------------------------------------------------------
# Dashboard Schemas
# ---------------------------------------------------------------

class DashboardStats(BaseModel):
    """Overall statistics for the dashboard."""
    total_jobs_analyzed: int
    total_scam_reports: int
    high_risk_jobs: int
    scam_percentage: float
    verified_recruiters: int
    blacklisted_domains: int
    jobs_last_7_days: int
    reports_last_7_days: int


class TrendData(BaseModel):
    """Monthly/weekly trend data point."""
    period: str
    scam_count: int
    total_count: int
    scam_percentage: float


class DashboardResponse(BaseModel):
    """Full dashboard data response."""
    stats: DashboardStats
    monthly_trends: List[TrendData]
    top_scam_keywords: List[dict]
    top_risk_companies: List[dict]
    recent_high_risk_jobs: List[dict]
    scam_by_type: List[dict]


# ---------------------------------------------------------------
# Job Post Schemas (for listing)
# ---------------------------------------------------------------

class JobPostSummary(BaseModel):
    """Summarized job post for list views."""
    job_id: UUID
    title: str
    company_name: Optional[str]
    location: Optional[str]
    scam_score: float
    risk_level: str
    is_flagged: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------
# Blacklist Schemas
# ---------------------------------------------------------------

class BlacklistEntry(BaseModel):
    """A single blacklisted entity."""
    entity_type: str
    entity_value: str
    reason: Optional[str]
    severity: str
    report_count: int


class BlacklistResponse(BaseModel):
    """Response from GET /blacklist"""
    domains: List[BlacklistEntry]
    emails: List[BlacklistEntry]
    companies: List[BlacklistEntry]
    total_count: int
