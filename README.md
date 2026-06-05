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
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── admin.html
│   ├── checker.html
│   ├── community.html
│   ├── reports.html
│   ├── dashboard.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   ├── api.js
│   │   └── chatbot.js
│   └── assets/
│       └── default-avatar.png
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   ├── .env
│   └── routes/
│       ├── __init__.py
│       ├── users.py
│       ├── jobs.py
│       ├── reports.py
│       ├── community.py
│       └── analyze.py
│
├── uploads/
│
└── database/
    └── schema.sql
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

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
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
