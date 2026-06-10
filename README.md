# 🛡️ ScamShield v5 – Fake Job Scam Detection Platform

India's most comprehensive job scam detection platform — AI-powered, community-driven, competition-ready.

---

## 🚀 Quick Start

```bash
# 1. Clone and install backend
cd backend && pip install -r requirements.txt

# 2. Copy environment variables
cp ../.env.example ../.env
# Edit .env with your Supabase URL and keys

# 3. Run backend
uvicorn main:app --reload --port 8000

# 4. Open frontend
# Just open frontend/index.html in your browser
# No build step needed — pure HTML/CSS/JS
```

---

## 🔐 Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@scamshield.in | Admin@2026 |
| **User** | demo@scamshield.in | Demo@2026 |

Or use the **"Demo User"** / **"Admin Demo"** buttons on the login page.

---

## 📁 Project Structure

```
scamshield-v5/
├── frontend/               # All HTML/CSS/JS (no build required)
│   ├── index.html          # Home – unified checker + live feed
│   ├── checker.html        # Full job analyzer (text/URL/screenshot/email/PDF)
│   ├── compare.html        # ⚖️ Comparison mode (UNIQUE FEATURE)
│   ├── live-feed.html      # 📡 Live scam feed with auto-scroll
│   ├── community.html      # 👥 Community reports with search
│   ├── login.html          # Auth page (user + admin)
│   ├── register.html       # 3-step registration
│   ├── profile.html        # User profile + activity
│   ├── my-reports.html     # User's own reports
│   ├── report.html         # File a scam report
│   ├── recruiter.html      # Recruiter email verifier
│   ├── domain-scanner.html # Domain WHOIS + SSL checker
│   ├── admin.html          # 📊 Admin dashboard (admin only)
│   ├── admin-users.html    # User management
│   ├── admin-reports.html  # Report moderation
│   ├── admin-jobs.html     # Job database manager
│   ├── admin-analytics.html # Full analytics
│   ├── admin-domains.html  # Blacklist manager
│   ├── admin-ml.html       # ML pipeline settings
│   ├── css/style.css       # Design system (dark/light)
│   └── js/
│       ├── main.js         # Core utilities, auth, API client
│       ├── sidebar.js      # Sidebar/topbar renderer
│       └── chatbot.js      # ScamGuard AI (Claude-powered)
│
├── backend/                # FastAPI Python backend
│   ├── main.py             # App entry point + route registration
│   ├── database.py         # Supabase/PostgreSQL connection
│   ├── config.py           # Settings from .env
│   ├── models/             # SQLAlchemy DB models + Pydantic schemas
│   ├── routes/             # analyze, auth, jobs, reports, domain
│   ├── ml/                 # Fraud detection engine + NLP + domain check
│   └── utils/              # Helpers, scraper
│
├── database/
│   ├── schema.sql          # Full DB schema (run on Supabase)
│   └── seed_data.sql       # Sample data for demo
│
└── .env.example            # All environment variables documented
```

---

## ✨ Key Features

### 🔍 Unified Scam Checker (Homepage)
One panel with 5 modes — hover/click to switch:
- **Link** – paste any job URL
- **Screenshot** – drag & drop WhatsApp/Naukri screenshot
- **Email** – upload email proof or enter sender address
- **Offer Letter** – PDF/DOCX analysis
- **Paste Text** – paste full job description

### 📡 Live Scam Feed
- Auto-scrolls, pauses on hover
- Color-coded dots: 🔴 High Risk · 🟠 Suspicious · 🟢 Safe
- Simulates WebSocket (30s polling in production)
- Filter by risk level, export as CSV

### ⚖️ Comparison Mode (UNIQUE)
Paste two URLs side by side:
- Every dimension shown with red/green diff
- AI summary explains why one is fake
- Perfect for "Is this TCS job real?" use case

### 📋 Job Trust Card
- Unique report ID (SS-2026-XXXXX)
- Risk score ring + per-dimension radar
- Share / Save / Report buttons
- Shareable as image for WhatsApp warnings

### 🤖 ScamGuard AI Chatbot
- Powered by Claude (Anthropic API)
- Falls back to keyword matching offline
- Context-aware conversation history
- Suggestion chips for quick queries

### 👥 Community Feed with Search
- Search by company, domain, job title
- Filter: All / Confirmed Scam / Suspicious / Recent / Popular
- Upvote, reply, share individual reports
- Trending companies sidebar

---

## 🔑 Supabase Setup

1. Create project at [supabase.com](https://supabase.com)
2. Go to Project Settings → API
3. Copy `Project URL` → `SUPABASE_URL`
4. Copy `anon public` key → `SUPABASE_ANON_KEY`
5. Go to Database → Connection String → copy URI → `DATABASE_URL`
6. Run `database/schema.sql` in Supabase SQL editor
7. Run `database/seed_data.sql` for sample data

---

## 👤 User vs Admin Panel

| Feature | User | Admin |
|---------|------|-------|
| Analyze jobs | ✅ | ✅ |
| Compare jobs | ✅ | ✅ |
| Live feed | ✅ | ✅ |
| Community feed | ✅ | ✅ |
| My profile | ✅ | — |
| My reports | ✅ | — |
| **Dashboard with stats** | ❌ | ✅ |
| **User management** | ❌ | ✅ |
| **Report moderation** | ❌ | ✅ |
| **Job database** | ❌ | ✅ |
| **Domain blacklist** | ❌ | ✅ |
| **ML settings** | ❌ | ✅ |
| **Analytics** | ❌ | ✅ |
