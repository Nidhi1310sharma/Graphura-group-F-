<<<<<<< HEAD
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
=======
# 🛡️ ScamShield – AI-Powered Fake Job Scam Detection Platform

India's comprehensive job and internship scam detection platform designed to help job seekers identify fraudulent opportunities, verify recruiters, analyze suspicious job postings, and contribute to a community-driven scam intelligence network.

---

## 🚀 Overview

ScamShield is a web-based platform that combines AI analysis, community reporting, recruiter verification, and domain intelligence to detect fake job and internship opportunities.

The platform enables users to:

* Analyze suspicious job postings
* Verify recruiter and company credibility
* Detect scam indicators in offer letters and emails
* Compare multiple job opportunities
* Report scams to help the community
* Track emerging recruitment fraud trends

The system is designed as a practical solution to improve awareness and safety for students, fresh graduates, and job seekers.
>>>>>>> backup-before-frontend-sync

---

## ✨ Key Features

<<<<<<< HEAD
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
=======
### 🔍 Unified Scam Checker

Analyze suspicious opportunities through multiple input methods:

* **Job Link Analysis** – Paste any job URL
* **Screenshot Analysis** – Upload WhatsApp, Telegram, LinkedIn, or Naukri screenshots
* **Email Verification** – Analyze recruiter emails and domains
* **Offer Letter Scanner** – Upload PDF/DOCX offer letters
* **Text Analysis** – Paste complete job descriptions

The platform evaluates multiple trust indicators and generates a risk score with explanations.

---

### ⚖️ Job Comparison Mode

Compare two job postings side-by-side.

Features include:

* Risk score comparison
* Company credibility comparison
* Domain analysis
* Red flag identification
* AI-generated summary explaining differences

Useful for questions such as:

> "Which of these two internship offers is legitimate?"

---

### 📋 Job Trust Card

Each analysis generates a detailed report containing:

* Unique Report ID
* Overall Risk Score
* Risk Category
* Domain Reputation
* Company Verification Status
* Recruiter Indicators
* Detected Scam Signals
* Community Reports Summary

Reports can be saved, shared, and revisited later.

---

### 📡 Live Scam Feed

Real-time feed displaying recently reported scams.

Features:

* Risk-level filters
* Company search
* Export functionality
* Trending scam activity monitoring

Risk Levels:

* 🔴 High Risk
* 🟠 Suspicious
* 🟢 Safe

---

### 👥 Community Forum

Users can:

* Share scam experiences
* Report fraudulent recruiters
* Discuss suspicious job offers
* Upvote helpful reports
* Search previous scam cases

The community database acts as a crowdsourced scam intelligence system.

---

### 🤖 ScamGuard AI Assistant

AI-powered chatbot for scam awareness and guidance.

Capabilities:

* Explain scam indicators
* Answer verification questions
* Guide users through analysis reports
* Provide safety recommendations
* Assist with platform navigation

---

### 👤 User Dashboard

Users can:

* View analysis history
* Manage reports
* Track saved investigations
* Update profile information
* Monitor account activity

---

### 🛠️ Admin Dashboard

Administrative tools for moderation and monitoring.

Features:

* User Management
* Report Moderation
* Scam Database Management
* Domain Blacklist Management
* Analytics Dashboard
* Community Monitoring
* System Configuration
* ML/Detection Settings

---

## 🏗️ System Architecture

### Frontend

* HTML5
* CSS3
* JavaScript (Vanilla JS)

### Backend

* Python
* FastAPI
* JWT Authentication

### Database

* PostgreSQL
* Supabase

### Additional Services

* Domain Reputation Analysis
* Email Verification
* Community Reporting System
* AI-based Risk Assessment

---

## 📂 Project Structure

```text
scamshield/
├── backend/
│   ├── admin/
│   │   ├── auth.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   │
│   ├── routes/
│   │   ├── analyze.py
│   │   ├── auth.py
│   │   ├── community.py
│   │   └── reports.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── community.py
│   │   └── reports.py
│   │
│   ├── auth.py
│   ├── main.py
│   ├── supabase_client.py
│   └── .env.example
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── checker.html
│   ├── compare.html
│   ├── community.html
│   ├── dashboard.html
│   ├── live-feed.html
│   ├── profile.html
│   ├── report.html
│   ├── settings.html
│   │
│   ├── admin.html
│   ├── admin-users.html
│   ├── admin-reports.html
│   ├── admin-jobs.html
│   ├── admin-domains.html
│   ├── admin-community.html
│   ├── admin-analytics.html
│   └── admin-ml.html
│
├── database/
│   ├── schema.sql
│   └── seed_data.sql
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🔐 Demo Credentials

### Admin Account

```text
Email: admin@scamshield.in
Password: Admin@2026
```

### Demo User

```text
Email: demo@scamshield.in
Password: Demo@2026
```

---

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd scamshield
```

---

### 2. Backend Setup

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Configure:

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
DATABASE_URL=
SECRET_KEY=
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend API:

```text
http://localhost:8000
```

---

### 3. Frontend Setup

Option 1: Open directly in browser

```text
frontend/index.html
```

Option 2: Use local server

```bash
cd frontend
python -m http.server 5500
```

Visit:

```text
http://localhost:5500
```

---

## 🗄️ Supabase Setup

1. Create a Supabase project
2. Open Project Settings → API
3. Copy:

```text
Project URL → SUPABASE_URL
Anon Key → SUPABASE_ANON_KEY
```

4. Open Database → Connection String

```text
URI → DATABASE_URL
```

5. Execute:

```sql
database/schema.sql
```

6. Seed sample data:

```sql
database/seed_data.sql
```

---

## 👥 User Roles

| Feature                 | User | Admin |
| ----------------------- | ---- | ----- |
| Analyze Jobs            | ✅    | ✅     |
| Compare Jobs            | ✅    | ✅     |
| Scam Feed               | ✅    | ✅     |
| Community Forum         | ✅    | ✅     |
| Submit Reports          | ✅    | ✅     |
| Profile Management      | ✅    | ❌     |
| Dashboard Statistics    | ❌    | ✅     |
| User Management         | ❌    | ✅     |
| Report Moderation       | ❌    | ✅     |
| Job Database Management | ❌    | ✅     |
| Domain Blacklist        | ❌    | ✅     |
| Analytics Dashboard     | ❌    | ✅     |
| ML Configuration        | ❌    | ✅     |

---

## 📌 Core Modules

### Scam Checker

Analyzes job postings and detects scam indicators.

### Recruiter Verification

Verifies recruiter credibility using available metadata and domain intelligence.

### Offer Letter Scanner

Checks uploaded offer letters for suspicious patterns.

### Domain Scanner

Analyzes domain age, registration information, trust indicators, and reputation signals.

### Community Intelligence

Collects user-generated scam reports and discussions.

### Reports Management

Stores and manages investigation reports.

### Analytics Dashboard

Provides insights into scam trends and platform activity.

### Administration Module

Moderation and system management tools.

---

## 🎯 Project Goal

The objective of ScamShield is to reduce job and internship fraud by combining:

* Automated scam detection
* Community intelligence
* Domain verification
* Recruiter analysis
* User education

This helps job seekers make safer decisions before sharing personal information, paying fees, or accepting offers.

---

## 👨‍💻 Team Project

Developed as a collaborative academic project focused on solving real-world recruitment fraud challenges through technology, community participation, and AI-assisted analysis.

---

## 📄 License

This project is intended for educational, academic, and research purposes.
>>>>>>> backup-before-frontend-sync
