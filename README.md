# 🛡️ ScamDetect

A web-based platform developed to help users identify fake job and internship opportunities. The system allows users to analyze suspicious job postings, report scams, participate in community discussions, and stay informed about common recruitment frauds.

## 🚀 Features

* Analyze job and internship postings for potential scams
* User registration and login system
* Community discussion forum
* Scam reporting and tracking
* Admin dashboard for moderation
* Interactive analytics dashboard
* Dark and Light mode support
* AI chatbot assistant for basic guidance

## 📂 Project Structure

```text
scam-detector/
├── backend/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── community.py
│   │   ├── jobs.py
│   │   ├── reports.py
│   │   ├── users.py
│   │   └── usersold.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── .env.example
│   ├── __init__.py
│   ├── auth.py
│   ├── main.py
│   ├── supabase_client.py
│   ├── test.py
│   ├── test_pwd.py
│   └── test_supabse_client.py
├── frontend/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── chatbot.js
│   │   └── main.js
│   ├── admin.html
│   ├── checker.html
│   ├── community.html
│   ├── dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   ├── register.html
│   └── reports.html
├── .gitignore
├── architechture.txt
├── generate_hash.py
├── README.md
└── requirements.txt

 
```

## 🛠️ Technologies Used

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* FastAPI
* JWT Authentication

### Database

* PostgreSQL / SQL

## ▶️ Running the Project

### Backend

Backend Setup

1. Copy backend/.env.example to backend/.env

2. Fill in:
   SUPABASE_URL
   SUPABASE_SERVICE_KEY
   SECRET_KEY

3. Install requirements:
```bash
   pip install -r requirements.txt
```

4. Run:
```bash
   python -m uvicorn backend.main:app --reload
```

### Frontend

Open the frontend folder using VS Code and run it using Live Server, or use:

```bash
python -m http.server 5500
```

Then visit:

```text
http://localhost:5500
```

## 📌 Main Modules

### Scam Checker

Allows users to analyze suspicious job postings using different input methods.

### Community Forum

Users can share experiences, discuss scams, and help others stay informed.

### Reports

Provides a platform to submit and review scam reports.

### Dashboard

Displays statistics, trends, and overall platform activity.

### Admin Panel

Used for managing users, reports, and moderation activities.

## 👨‍💻 Team Project

This project was developed as part of a collaborative effort to create a practical solution for identifying fake internship and job opportunities and improving awareness among job seekers.

## 📄 License

This project is developed for educational and academic purposes.
