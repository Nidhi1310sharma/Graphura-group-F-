-- ============================================================
-- COMPLETE DATABASE SCHEMA - Run this in Supabase SQL Editor
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    profile_image TEXT DEFAULT '/assets/default-avatar.png',
    phone_number TEXT,
    skills TEXT[] DEFAULT '{}',
    experience_years INTEGER DEFAULT 0,
    education TEXT,
    location TEXT,
    bio TEXT,
    role TEXT DEFAULT 'user', -- user / admin / moderator
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- USER SESSIONS
-- ============================================================
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- USER ACTIVITIES
-- ============================================================
CREATE TABLE user_activities (
    activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type TEXT, -- job_checked / scam_reported / recruiter_verified / job_applied / comment
    job_id UUID,
    report_id UUID,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- JOB POSTS
-- ============================================================
CREATE TABLE job_posts (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    company_name TEXT,
    salary TEXT,
    location TEXT,
    description TEXT,
    posted_date DATE,
    days_left INTEGER,
    source_url TEXT,
    domain_url TEXT,
    company_contact TEXT,
    domain_age_days INTEGER,
    ssl_certificate TEXT,
    whois_info TEXT,
    scam_report TEXT DEFAULT 'No',
    job_type TEXT,
    work_mode TEXT,
    skills_required TEXT,
    eligibility TEXT,
    company_linkedin TEXT,
    company_website TEXT,
    data_source TEXT,
    scam_score FLOAT DEFAULT 0,
    risk_level TEXT DEFAULT 'UNKNOWN',
    analyzed_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SCAM REPORTS (with evidence)
-- ============================================================
CREATE TABLE scam_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reported_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    reporter_name TEXT,
    company_name TEXT NOT NULL,
    job_title TEXT,
    job_url TEXT,
    description TEXT,
    evidence_type TEXT, -- description / screenshot / link / offer_letter
    evidence_url TEXT,
    evidence_text TEXT,
    scam_type TEXT, -- fee_fraud / phishing / fake_company / data_theft / impersonation
    severity INTEGER DEFAULT 2,
    status TEXT DEFAULT 'pending',
    admin_notes TEXT,
    reviewed_by UUID REFERENCES users(user_id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- COMMUNITY POSTS
-- ============================================================
CREATE TABLE community_posts (
    post_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    user_name TEXT,
    user_image TEXT,
    content TEXT NOT NULL,
    scam_report_id UUID REFERENCES scam_reports(report_id) ON DELETE SET NULL,
    likes INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- COMMUNITY LIKES
-- ============================================================
CREATE TABLE community_likes (
    like_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES community_posts(post_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- ============================================================
-- COMMUNITY COMMENTS
-- ============================================================
CREATE TABLE community_comments (
    comment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES community_posts(post_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    user_name TEXT,
    user_image TEXT,
    content TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- BLACKLISTED ENTITIES
-- ============================================================
CREATE TABLE blacklisted_entities (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL, -- domain / email / company / phone
    entity_value TEXT NOT NULL,
    reason TEXT,
    reported_by UUID REFERENCES users(user_id),
    severity TEXT DEFAULT 'medium',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_value)
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_sessions_token ON user_sessions(token);
CREATE INDEX idx_reports_status ON scam_reports(status);
CREATE INDEX idx_reports_reported_by ON scam_reports(reported_by);
CREATE INDEX idx_posts_created ON community_posts(created_at DESC);
CREATE INDEX idx_posts_user ON community_posts(user_id);
CREATE INDEX idx_comments_post ON community_comments(post_id);
CREATE INDEX idx_blacklisted_active ON blacklisted_entities(active, entity_type);

-- ============================================================
-- INSERT DEFAULT ADMIN USER (password: admin123)
-- Use this to create admin user - hash will be set by backend
-- ============================================================
-- Admin user will be created via API on first run

-- ============================================================
-- VIEWS
-- ============================================================

-- Recent scam reports view
CREATE OR REPLACE VIEW recent_scam_reports AS
SELECT 
    r.report_id,
    r.company_name,
    r.job_title,
    r.scam_type,
    r.severity,
    r.status,
    u.full_name as reporter_name,
    u.profile_image as reporter_image,
    r.created_at
FROM scam_reports r
LEFT JOIN users u ON r.reported_by = u.user_id
WHERE r.status != 'rejected'
ORDER BY r.created_at DESC
LIMIT 50;

-- Community feed view
CREATE OR REPLACE VIEW community_feed AS
SELECT 
    p.post_id,
    p.user_id,
    p.user_name,
    p.user_image,
    p.content,
    p.likes,
    p.comments_count,
    p.created_at,
    r.company_name as scam_company,
    r.scam_type
FROM community_posts p
LEFT JOIN scam_reports r ON p.scam_report_id = r.report_id
ORDER BY p.created_at DESC;