# Placement Preparation & Tracking System

A Flask web application for a college placement cell to manage placement drives, student applications, preparation resources, practice tests, and NAAC/NBA placement reporting.

## Features

- Student and TPO/admin authentication with role-based access control
- Student registration, profile editing, and PDF resume uploads
- Company and placement-drive CRUD management
- Eligibility checking and student applications with status pipelines
- Preparation resources, MCQ tests, scoring, and attempt history
- Live admin dashboard, reports, placement analytics, and NAAC/NBA CSV exports
- Admin student management, application workflow, preparation CRUD, and bulk question import
- Admin profile/password updates, administrator management, and a latest-50 audit trail
- Responsive Bootstrap admin shell with mobile sidebar navigation and confirmation dialogs

## Setup

Python 3 is required.

```bash
cd placement_system
pip install -r requirements.txt
python seed.py
python app.py
```

Open `http://127.0.0.1:5000/`.

Running `seed.py` resets the SQLite database and restores the sample data.

## Default Credentials

| Role | Email | Password |
|---|---|---|
| Admin/TPO | `admin@college.edu` | `admin123` |
| Student | `cse2026001@college.edu` | `student123` |

## Folder Structure

```text
placement_system/
├── app.py
├── config.py
├── models.py
├── seed.py
├── requirements.txt
├── decorators.py
├── routes/
├── services/
├── templates/
└── static/
```
