from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
import re

from models import Student, User, db


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        roll_no = request.form.get("roll_no", "").strip()
        branch = request.form.get("branch", "")
        cgpa_text = request.form.get("cgpa", "")
        backlogs_text = request.form.get("active_backlogs", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = False

        if not all([name, email, roll_no, branch, cgpa_text, backlogs_text, password, confirm_password]):
            flash("All registration fields are required.", "danger")
            error = True

        if len(name) < 2 or len(name) > 120:
            flash("Name must be between 2 and 120 characters.", "danger")
            error = True

        if len(email) > 255:
            flash("Email must not exceed 255 characters.", "danger")
            error = True

        if not re.fullmatch(r"\d{1,13}", roll_no):
            flash("Roll number must contain only digits and not exceed 13 digits.", "danger")
            error = True

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            error = True

        if Student.query.filter_by(roll_no=roll_no).first():
            flash("This roll number is already registered.", "danger")
            error = True

        try:
            cgpa = float(cgpa_text)
            if cgpa < 0 or cgpa > 10:
                flash("CGPA must be between 0 and 10.", "danger")
                error = True
        except (TypeError, ValueError):
            flash("CGPA must be a valid number.", "danger")
            cgpa = None
            error = True

        try:
            backlogs = int(backlogs_text)
            if backlogs < 0 or backlogs > 40:
                flash("Active backlogs must be between 0 and 40.", "danger")
                error = True
        except (TypeError, ValueError):
            flash("Active backlogs must be a whole number.", "danger")
            backlogs = None
            error = True

        if branch not in {"CSE", "AIML", "IT", "ECE", "ME"}:
            flash("Please select a valid branch.", "danger")
            error = True

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            error = True
        elif len(password) < 6 or len(password) > 128:
            flash("Password must be between 6 and 128 characters.", "danger")
            error = True
        elif password.strip() == "":
            flash("Password cannot be blank or contain only spaces.", "danger")
            error = True

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "danger")
            error = True

        if not error:
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role="student",
            )
            student = Student(
                roll_no=roll_no,
                branch=branch,
                cgpa=cgpa,
                active_backlogs=backlogs,
                resume_filename=None,
            )
            user.student = student
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        if current_user.role == "student":
            return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")
        if len(email) > 255:
            flash("Email is too long.", "danger")
            return render_template("login.html")
        if len(password) > 128 or password.strip() == "":
            flash("Invalid email or password.", "danger")
            return render_template("login.html")
        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("Invalid email or password.", "danger")
        elif not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
        else:
            login_user(user)
            flash("Login successful. Welcome, " + user.name + "!", "success")
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            if user.role == "student":
                return redirect(url_for("student.dashboard"))
            flash("Your account has an invalid role.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))
