-- ============================================================
-- ScamShield v4 – Full PostgreSQL Database Schema
-- Supports: Users, Jobs, Reports, Community, Admin, Analytics
-- Run this before seed_data.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLE: users – registered platform users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    mobile          TEXT,
    city            TEXT,
    profession      TEXT,
    bio             TEXT,
    avatar_url      TEXT,                       -- stored image URL or base64
    skills          TEXT[],                     -- array of skill strings
    role            TEXT DEFAULT 'user',        -- user / admin
    is_active       BOOLEAN DEFAULT TRUE,
    is_banned       BOOLEAN DEFAULT FALSE,
    ban_reason      TEXT,
    email_verified  BOOLEAN DEFAULT FALSE,
    reports_count   INT DEFAULT 0,
    checks_count    INT DEFAULT 0,
    upvotes_received INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    last_login      TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: job_posts
-- ============================================================
CREATE TABLE IF NOT EXISTS job_posts (
    job_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    company_name    TEXT,
    salary_min      NUMERIC,
    salary_max      NUMERIC,
    salary_text     TEXT,
    location        TEXT,
    description     TEXT,
    posted_date     DATE,
    source_url      TEXT,
    domain_name     TEXT,
    recruiter_email TEXT,
    contact_phone   TEXT,
    source_platform TEXT DEFAULT 'user_submitted',
    scam_score      FLOAT DEFAULT 0.0,
    risk_level      TEXT DEFAULT 'UNKNOWN',
    is_flagged      BOOLEAN DEFAULT FALSE,
    is_verified     BOOLEAN DEFAULT FALSE,
    keyword_score   FLOAT DEFAULT 0.0,
    domain_score    FLOAT DEFAULT 0.0,
    salary_score    FLOAT DEFAULT 0.0,
    grammar_score   FLOAT DEFAULT 0.0,
    analyzed_at     TIMESTAMP,
    submitted_by    UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: scam_reports – user-submitted reports
-- ============================================================
CREATE TABLE IF NOT EXISTS scam_reports (
    report_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID REFERENCES job_posts(job_id) ON DELETE SET NULL,
    company_name    TEXT,
    job_title       TEXT,
    job_url         TEXT,
    scam_type       TEXT,
    report_reason   TEXT NOT NULL,
    user_comment    TEXT,
    severity        INT DEFAULT 1,
    screenshot_url  TEXT,
    email_proof_url TEXT,
    offer_pdf_url   TEXT,
    reporter_id     UUID REFERENCES users(user_id) ON DELETE SET NULL,
    reporter_email  TEXT,
    reporter_name   TEXT,
    status          TEXT DEFAULT 'pending',     -- pending/reviewed/confirmed/rejected
    admin_notes     TEXT,
    upvotes         INT DEFAULT 0,
    reported_at     TIMESTAMP DEFAULT NOW(),
    reviewed_at     TIMESTAMP,
    reviewed_by     UUID REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: community_posts – social feed
-- ============================================================
CREATE TABLE IF NOT EXISTS community_posts (
    post_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID REFERENCES scam_reports(report_id) ON DELETE CASCADE,
    author_id       UUID REFERENCES users(user_id) ON DELETE SET NULL,
    author_name     TEXT,
    company_name    TEXT,
    job_title       TEXT,
    domain          TEXT,
    salary_offered  TEXT,
    post_type       TEXT DEFAULT 'scam',        -- scam / suspicious / warning
    body            TEXT NOT NULL,
    upvotes         INT DEFAULT 0,
    reply_count     INT DEFAULT 0,
    is_visible      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: community_replies
-- ============================================================
CREATE TABLE IF NOT EXISTS community_replies (
    reply_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id         UUID REFERENCES community_posts(post_id) ON DELETE CASCADE,
    author_id       UUID REFERENCES users(user_id) ON DELETE SET NULL,
    author_name     TEXT,
    body            TEXT NOT NULL,
    upvotes         INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: post_upvotes – prevent double voting
-- ============================================================
CREATE TABLE IF NOT EXISTS post_upvotes (
    upvote_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id         UUID REFERENCES community_posts(post_id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(user_id) ON DELETE CASCADE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- ============================================================
-- TABLE: domain_reputation
-- ============================================================
CREATE TABLE IF NOT EXISTS domain_reputation (
    domain_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_name     TEXT UNIQUE NOT NULL,
    domain_age_days INT,
    ssl_valid       BOOLEAN DEFAULT FALSE,
    trust_score     FLOAT DEFAULT 50.0,
    blacklisted     BOOLEAN DEFAULT FALSE,
    blacklist_source TEXT,
    whois_registrar TEXT,
    whois_country   TEXT,
    suspicious_pattern BOOLEAN DEFAULT FALSE,
    report_count    INT DEFAULT 0,
    last_checked    TIMESTAMP DEFAULT NOW(),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: recruiter_profiles
-- ============================================================
CREATE TABLE IF NOT EXISTS recruiter_profiles (
    recruiter_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_name  TEXT,
    email           TEXT UNIQUE,
    company         TEXT,
    linkedin_url    TEXT,
    domain_name     TEXT,
    phone           TEXT,
    verified        BOOLEAN DEFAULT FALSE,
    blacklisted     BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    previous_reports INT DEFAULT 0,
    trust_score     FLOAT DEFAULT 50.0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: blacklisted_entities
-- ============================================================
CREATE TABLE IF NOT EXISTS blacklisted_entities (
    entity_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     TEXT NOT NULL,              -- domain/email/company/phone
    entity_value    TEXT NOT NULL,
    reason          TEXT,
    report_count    INT DEFAULT 1,
    severity        TEXT DEFAULT 'medium',
    source          TEXT DEFAULT 'user_report',
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_value)
);

-- ============================================================
-- TABLE: flagged_keywords
-- ============================================================
CREATE TABLE IF NOT EXISTS flagged_keywords (
    keyword_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword         TEXT UNIQUE NOT NULL,
    fraud_weight    FLOAT NOT NULL,
    category        TEXT,
    language        TEXT DEFAULT 'en',
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: user_activity_log
-- ============================================================
CREATE TABLE IF NOT EXISTS user_activity_log (
    activity_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type   TEXT NOT NULL,              -- scan/report/upvote/login/register
    reference_id    UUID,
    reference_type  TEXT,
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: analytics_events
-- ============================================================
CREATE TABLE IF NOT EXISTS analytics_events (
    event_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      TEXT NOT NULL,
    scam_score      FLOAT,
    risk_level      TEXT,
    platform        TEXT,
    location        TEXT,
    user_id         UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_job_posts_scam_score ON job_posts(scam_score DESC);
CREATE INDEX IF NOT EXISTS idx_job_posts_domain ON job_posts(domain_name);
CREATE INDEX IF NOT EXISTS idx_job_posts_created_at ON job_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scam_reports_status ON scam_reports(status);
CREATE INDEX IF NOT EXISTS idx_scam_reports_reported_at ON scam_reports(reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_posts_created_at ON community_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_posts_upvotes ON community_posts(upvotes DESC);
CREATE INDEX IF NOT EXISTS idx_community_replies_post_id ON community_replies(post_id);
CREATE INDEX IF NOT EXISTS idx_blacklisted_active ON blacklisted_entities(active, entity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity_log(user_id, created_at DESC);

-- ============================================================
-- VIEWS
-- ============================================================
CREATE OR REPLACE VIEW high_risk_jobs AS
SELECT job_id, title, company_name, scam_score, risk_level, domain_name, created_at
FROM job_posts WHERE scam_score >= 61 ORDER BY scam_score DESC;

CREATE OR REPLACE VIEW dashboard_stats AS
SELECT
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN is_flagged = TRUE THEN 1 END) as flagged_jobs,
    COUNT(CASE WHEN scam_score >= 61 THEN 1 END) as high_risk_jobs,
    ROUND(AVG(scam_score)::numeric, 2) as avg_scam_score,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as jobs_last_7_days
FROM job_posts;

CREATE OR REPLACE VIEW community_feed AS
SELECT 
    cp.post_id, cp.body, cp.post_type, cp.upvotes, cp.reply_count, cp.created_at,
    cp.company_name, cp.job_title, cp.domain, cp.salary_offered,
    u.full_name as author_name, u.avatar_url as author_avatar, u.city as author_city
FROM community_posts cp
LEFT JOIN users u ON cp.author_id = u.user_id
WHERE cp.is_visible = TRUE
ORDER BY cp.created_at DESC;

-- Function to auto-blacklist after 3 confirmed reports
CREATE OR REPLACE FUNCTION auto_blacklist_company()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'confirmed' THEN
        INSERT INTO blacklisted_entities (entity_type, entity_value, reason, report_count, severity, source)
        VALUES ('company', NEW.company_name, 'Auto-blacklisted after multiple confirmed reports', 
                (SELECT COUNT(*) FROM scam_reports WHERE company_name = NEW.company_name AND status = 'confirmed'),
                'high', 'auto_detected')
        ON CONFLICT (entity_type, entity_value) DO UPDATE
        SET report_count = EXCLUDED.report_count, updated_at = NOW()
        WHERE blacklisted_entities.entity_type = 'company';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at column to blacklisted_entities if needed
ALTER TABLE blacklisted_entities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Trigger
DROP TRIGGER IF EXISTS trigger_auto_blacklist ON scam_reports;
CREATE TRIGGER trigger_auto_blacklist
    AFTER UPDATE ON scam_reports
    FOR EACH ROW EXECUTE FUNCTION auto_blacklist_company();

COMMENT ON TABLE users IS 'Registered platform users with full profile data';
COMMENT ON TABLE job_posts IS 'All job postings with AI scam scores';
COMMENT ON TABLE scam_reports IS 'User-submitted scam reports with proof attachments';
COMMENT ON TABLE community_posts IS 'Community feed posts about scam experiences';
COMMENT ON TABLE community_replies IS 'Replies to community posts';
