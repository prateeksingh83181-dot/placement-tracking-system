from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint


db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    student = db.relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="ck_user_role"),
    )


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    branch = db.Column(db.String(10), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    active_backlogs = db.Column(db.Integer, nullable=False, default=0)
    resume_filename = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="student")
    applications = db.relationship("Application", back_populates="student", cascade="all, delete-orphan")
    practice_attempts = db.relationship("PracticeAttempt", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("branch IN ('CSE', 'AIML', 'IT', 'ECE', 'ME')", name="ck_student_branch"),
    )


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role_title = db.Column(db.String(150), nullable=False)
    package_lpa = db.Column(db.Float, nullable=False)
    allowed_branches = db.Column(db.String(255), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    max_backlogs = db.Column(db.Integer, nullable=False)
    drive_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)

    applications = db.relationship("Application", back_populates="company", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('Open', 'Screening', 'Interview', 'Closed')", name="ck_company_status"),
    )


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    link_or_text = db.Column(db.Text, nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    added_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin = db.relationship("User")

    __table_args__ = (
        CheckConstraint("category IN ('Aptitude', 'Coding', 'Interview', 'Resume')", name="ck_resource_category"),
    )


class PracticeQuestion(db.Model):
    __tablename__ = "practice_questions"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

    __table_args__ = (
        CheckConstraint("category IN ('Aptitude', 'Coding', 'Interview', 'Resume')", name="ck_question_category"),
        CheckConstraint("correct_option IN ('A', 'B', 'C', 'D')", name="ck_question_correct_option"),
    )


class PracticeAttempt(db.Model):
    __tablename__ = "practice_attempts"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    category = db.Column(db.String(20), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    taken_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="practice_attempts")


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin = db.relationship("User")


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Applied")
    applied_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship("Student", back_populates="applications")
    company = db.relationship("Company", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("student_id", "company_id", name="uq_application_student_company"),
        CheckConstraint(
            "status IN ('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected')",
            name="ck_application_status",
        ),
    )
