# ============================================================
# models/db_models.py - SQLAlchemy ORM Models
# These Python classes map to PostgreSQL tables
# ============================================================

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, Integer,
    Text, DateTime, Date, Numeric, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base


class JobPost(Base):
    """
    Represents a job/internship posting.
    Stores the raw data + fraud analysis scores.
    """
    __tablename__ = "job_posts"

    job_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title           = Column(Text, nullable=False)
    company_name    = Column(Text)
    salary_min      = Column(Numeric)
    salary_max      = Column(Numeric)
    salary_text     = Column(Text)
    location        = Column(Text)
    description     = Column(Text)
    posted_date     = Column(Date)
    source_url      = Column(Text)
    domain_name     = Column(Text)
    recruiter_email = Column(Text)
    contact_phone   = Column(Text)
    source_platform = Column(Text)          # internshala / linkedin / user_submitted / etc.

    # --- Fraud Score Fields ---
    scam_score      = Column(Float, default=0.0)
    risk_level      = Column(String(20), default="UNKNOWN")
    is_flagged      = Column(Boolean, default=False)
    is_verified     = Column(Boolean, default=False)
    keyword_score   = Column(Float, default=0.0)
    domain_score    = Column(Float, default=0.0)
    salary_score    = Column(Float, default=0.0)
    grammar_score   = Column(Float, default=0.0)
    analyzed_at     = Column(DateTime)

    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: one job can have many reports
    reports = relationship("ScamReport", back_populates="job_post")


class RecruiterProfile(Base):
    """
    Recruiter and company profiles.
    Tracks verification status and fraud history.
    """
    __tablename__ = "recruiter_profiles"

    recruiter_id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_name   = Column(Text)
    email            = Column(Text, unique=True)
    company          = Column(Text)
    linkedin_url     = Column(Text)
    domain_name      = Column(Text)
    phone            = Column(Text)
    verified         = Column(Boolean, default=False)
    blacklisted      = Column(Boolean, default=False)
    blacklist_reason = Column(Text)
    previous_reports = Column(Integer, default=0)
    trust_score      = Column(Float, default=50.0)  # 0-100
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScamReport(Base):
    """
    User-submitted scam reports.
    Links to job posts where possible.
    """
    __tablename__ = "scam_reports"

    report_id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id         = Column(UUID(as_uuid=True), ForeignKey("job_posts.job_id"), nullable=True)
    company_name   = Column(Text)
    job_title      = Column(Text)
    job_url        = Column(Text)
    scam_type      = Column(Text)           # fee_demand / phishing / fake_company / etc.
    report_reason  = Column(Text, nullable=False)
    user_comment   = Column(Text)
    severity       = Column(Integer, default=1)  # 1-4
    screenshot_url = Column(Text)
    reporter_email = Column(Text)
    reporter_name  = Column(Text)
    status         = Column(String(20), default="pending")  # pending/reviewed/confirmed/rejected
    admin_notes    = Column(Text)
    reported_at    = Column(DateTime, default=datetime.utcnow)
    reviewed_at    = Column(DateTime)

    # Relationship back to job post
    job_post = relationship("JobPost", back_populates="reports")


class DomainReputation(Base):
    """
    Domain analysis and reputation data.
    Cached to avoid repeated external API calls.
    """
    __tablename__ = "domain_reputation"

    domain_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_name        = Column(Text, unique=True, nullable=False)
    domain_age_days    = Column(Integer)
    ssl_valid          = Column(Boolean, default=False)
    trust_score        = Column(Float, default=0.5)     # 0-1
    blacklisted        = Column(Boolean, default=False)
    blacklist_source   = Column(Text)
    whois_registrar    = Column(Text)
    whois_country      = Column(Text)
    suspicious_pattern = Column(Boolean, default=False)
    report_count       = Column(Integer, default=0)
    last_checked       = Column(DateTime, default=datetime.utcnow)
    created_at         = Column(DateTime, default=datetime.utcnow)


class FlaggedKeyword(Base):
    """
    NLP fraud keyword dictionary.
    Each keyword has a fraud_weight (0-1) indicating how suspicious it is.
    """
    __tablename__ = "flagged_keywords"

    keyword_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword      = Column(Text, unique=True, nullable=False)
    fraud_weight = Column(Float, nullable=False)
    category     = Column(Text)     # fee / urgency / fake_offer / phishing / communication
    language     = Column(String(5), default="en")
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class BlacklistedEntity(Base):
    """
    Blacklisted domains, emails, companies, and phone numbers.
    """
    __tablename__ = "blacklisted_entities"

    entity_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type  = Column(Text, nullable=False)     # domain / email / company / phone
    entity_value = Column(Text, nullable=False)
    reason       = Column(Text)
    report_count = Column(Integer, default=1)
    severity     = Column(Text, default="medium")   # low / medium / high / critical
    source       = Column(Text, default="user_report")
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class AnalyticsEvent(Base):
    """
    Tracks user actions for the analytics dashboard.
    No personal data (PII) stored here.
    """
    __tablename__ = "analytics_events"

    event_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(Text, nullable=False)   # scan / report / recruiter_check
    scam_score = Column(Float)
    risk_level = Column(Text)
    platform   = Column(Text)
    location   = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """
    Registered users for future authentication.
    """
    __tablename__ = "users"

    user_id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email        = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name    = Column(Text)
    role         = Column(String(20), default="user")   # user / reporter / analyst / admin
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    last_login   = Column(DateTime)
