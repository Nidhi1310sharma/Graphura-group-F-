# backend/models.py
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    profile_image = Column(String, default="/assets/default-avatar.png")
    phone_number = Column(String, nullable=True)
    skills = Column(ARRAY(String), default=[])
    experience_years = Column(Integer, default=0)
    education = Column(String, nullable=True)
    location = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobPost(Base):
    __tablename__ = "job_posts"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    days_left = Column(Integer, nullable=True)
    source_url = Column(String, nullable=True)
    domain_url = Column(String, nullable=True)
    company_contact = Column(String, nullable=True)
    domain_age_days = Column(Integer, nullable=True)
    ssl_certificate = Column(String, nullable=True)
    whois_info = Column(Text, nullable=True)
    scam_report = Column(String, default="No")
    job_type = Column(String, nullable=True)
    work_mode = Column(String, nullable=True)
    skills_required = Column(String, nullable=True)
    eligibility = Column(String, nullable=True)
    company_linkedin = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    data_source = Column(String, nullable=True)
    scam_score = Column(Float, default=0)
    risk_level = Column(String, default="UNKNOWN")
    recruiter_email = Column(String, nullable=True)
    analyzed_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScamReport(Base):
    __tablename__ = "scam_reports"
    
    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reported_by = Column(UUID(as_uuid=True), nullable=True)
    reporter_name = Column(String, nullable=True)
    company_name = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    job_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    evidence_type = Column(String, nullable=True)
    evidence_url = Column(String, nullable=True)
    evidence_text = Column(Text, nullable=True)
    scam_type = Column(String, default="other")
    severity = Column(Integer, default=2)
    status = Column(String, default="pending")
    admin_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityPost(Base):
    __tablename__ = "community_posts"
    
    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String, nullable=True)
    user_image = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    scam_report_id = Column(UUID(as_uuid=True), nullable=True)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CommunityLike(Base):
    __tablename__ = "community_likes"
    
    like_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityComment(Base):
    __tablename__ = "community_comments"
    
    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String, nullable=True)
    user_image = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    activity_type = Column(String, nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    report_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BlacklistedEntity(Base):
    __tablename__ = "blacklisted_entities"
    
    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String, nullable=False)
    entity_value = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    reported_by = Column(UUID(as_uuid=True), nullable=True)
    severity = Column(String, default="medium")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)