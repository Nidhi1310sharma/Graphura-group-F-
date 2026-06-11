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

---

## ✨ Key Features

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
