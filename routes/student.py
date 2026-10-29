import os
import re
import random

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from decorators import role_required
from models import Application, Company, PracticeAttempt, PracticeQuestion, Resource, User, db
from services.eligibility import check_eligibility


student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():
    student = current_user.student
    open_companies = Company.query.filter_by(status="Open").order_by(Company.drive_date.asc()).all()
    applications = Application.query.filter_by(student_id=student.id).all()
    applied_company_ids = {application.company_id for application in applications}

    drive_cards = []
    eligible_count = 0
    for company in open_companies:
        is_eligible, reason = check_eligibility(student, company)
        if is_eligible:
            eligible_count += 1
        drive_cards.append({
            "company": company,
            "is_eligible": is_eligible,
            "reason": reason,
            "applied": company.id in applied_company_ids,
        })

    return render_template(
        "student/dashboard.html",
        student=student,
        drive_cards=drive_cards,
        eligible_count=eligible_count,
        application_count=len(applications),
    )


@student_bp.route("/apply/<int:company_id>", methods=["POST"])
@role_required("student")
def apply_to_company(company_id):
    student = current_user.student
    company = db.session.get(Company, company_id)

    if company is None:
        flash("Company or drive not found.", "danger")
        return redirect(url_for("student.dashboard"))

    if company.status != "Open":
        flash("Applications are only accepted for open drives.", "danger")
        return redirect(url_for("student.dashboard"))

    existing = Application.query.filter_by(
        student_id=student.id,
        company_id=company.id,
    ).first()
    if existing:
        flash("You have already applied to this company.", "warning")
        return redirect(url_for("student.dashboard"))

    is_eligible, reason = check_eligibility(student, company)
    if not is_eligible:
        flash(f"Application rejected: {reason}.", "danger")
        return redirect(url_for("student.dashboard"))

    application = Application(
        student_id=student.id,
        company_id=company.id,
        status="Applied",
    )
    db.session.add(application)
    db.session.commit()
    flash(f"Application submitted successfully to {company.name}.", "success")
    return redirect(url_for("student.dashboard"))


@student_bp.route("/profile", methods=["GET", "POST"])
@role_required("student")
def profile():
    student = current_user.student

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        cgpa_text = request.form.get("cgpa", "")
        backlogs_text = request.form.get("active_backlogs", "")
        error = False

        existing_user = User.query.filter_by(email=email).first() if email else None
        if existing_user and existing_user.id != current_user.id:
            flash("An account with this email already exists.", "danger")
            error = True

        if not email:
            flash("Email is required.", "danger")
            error = True
        elif len(email) > 255 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "danger")
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

        resume: FileStorage = request.files.get("resume")
        resume_filename = student.resume_filename
        has_resume_upload = bool(resume and resume.filename)
        if has_resume_upload:
            filename = secure_filename(resume.filename)
            if not filename.lower().endswith(".pdf"):
                flash("Resume must be a PDF file.", "danger")
                error = True
            else:
                resume.seek(0, os.SEEK_END)
                size = resume.tell()
                resume.seek(0)
                if size > 2 * 1024 * 1024:
                    flash("Resume must not exceed 2 MB.", "danger")
                    error = True
                elif size == 0:
                    flash("Resume file cannot be empty.", "danger")
                    error = True
                else:
                    header = resume.stream.read(5)
                    resume.seek(0)
                    if header != b"%PDF-":
                        flash("Resume must contain valid PDF data.", "danger")
                        error = True
                    else:
                        roll_no = secure_filename(student.roll_no)
                        resume_filename = secure_filename(f"{roll_no}_{filename}")

        if not error:
            old_resume = student.resume_filename
            current_user.email = email
            student.cgpa = cgpa
            student.active_backlogs = backlogs

            if has_resume_upload:
                os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
                new_path = os.path.join(current_app.config["UPLOAD_FOLDER"], resume_filename)
                resume.save(new_path)
                student.resume_filename = resume_filename

                if old_resume:
                    old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], old_resume)
                    if os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(new_path):
                        os.remove(old_path)

            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("student.profile"))

    return render_template("student/profile.html", student=student)


@student_bp.route("/profile/resume/<path:filename>")
@role_required("student")
def download_resume(filename):
    student = current_user.student
    if student.resume_filename != filename:
        flash("Resume not found.", "danger")
        return redirect(url_for("student.profile"))

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True,
    )


@student_bp.route("/applications")
@role_required("student")
def applications():
    student = current_user.student
    student_applications = (
        Application.query.filter_by(student_id=student.id)
        .join(Company)
        .order_by(Application.updated_on.desc())
        .all()
    )
    return render_template(
        "student/applications.html",
        applications=student_applications,
    )


PREPARATION_CATEGORIES = ["Aptitude", "Coding", "Interview", "Resume"]


@student_bp.route("/prepare")
@role_required("student")
def prepare():
    resources_by_category = {}
    for category in PREPARATION_CATEGORIES:
        resources_by_category[category] = (
            Resource.query.filter_by(category=category)
            .order_by(Resource.title.asc())
            .all()
        )

    attempts = (
        PracticeAttempt.query.filter_by(student_id=current_user.student.id)
        .order_by(PracticeAttempt.taken_on.desc())
        .all()
    )
    test_categories = [
        category for category in PREPARATION_CATEGORIES
        if PracticeQuestion.query.filter_by(category=category).count() >= 10
    ]
    return render_template(
        "student/prepare.html",
        resources_by_category=resources_by_category,
        categories=PREPARATION_CATEGORIES,
        test_categories=test_categories,
        attempts=attempts,
    )


@student_bp.route("/prepare/test", methods=["GET", "POST"])
@role_required("student")
def prepare_test():
    category = request.values.get("category", "")

    if request.method == "GET":
        if category not in PREPARATION_CATEGORIES:
            flash("Please choose a valid practice category.", "danger")
            return redirect(url_for("student.prepare"))

        pool = PracticeQuestion.query.filter_by(category=category).all()
        if len(pool) < 10:
            flash(f"This category needs 10 questions; only {len(pool)} are available.", "danger")
            return redirect(url_for("student.prepare"))

        questions = random.sample(pool, 10)
        session["practice_test_ids"] = [question.id for question in questions]
        session["practice_test_category"] = category
        return render_template("student/practice_test.html", category=category, questions=questions, result=None)

    question_ids = session.pop("practice_test_ids", [])
    test_category = session.pop("practice_test_category", category)
    questions = []
    score = 0
    results = []

    for question_id in question_ids:
        question = db.session.get(PracticeQuestion, question_id)
        if question is None:
            continue
        answer = request.form.get(f"question_{question.id}", "")
        is_correct = answer == question.correct_option
        if is_correct:
            score += 1
        questions.append(question)
        results.append({"question": question, "answer": answer, "correct": is_correct})

    if not questions:
        flash("The practice test has expired. Please start a new test.", "danger")
        return redirect(url_for("student.prepare"))

    attempt = PracticeAttempt(
        student_id=current_user.student.id,
        category=test_category,
        score=score,
        total=len(questions),
    )
    db.session.add(attempt)
    db.session.commit()

    attempts = (
        PracticeAttempt.query.filter_by(student_id=current_user.student.id)
        .order_by(PracticeAttempt.taken_on.desc())
        .all()
    )
    flash(f"Practice test submitted. You scored {score}/{len(questions)}.", "success")
    return render_template(
        "student/practice_test.html",
        category=test_category,
        questions=questions,
        result={"score": score, "total": len(questions), "results": results},
        attempts=attempts,
    )
