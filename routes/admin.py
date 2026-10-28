import csv
import os
from datetime import datetime
from io import StringIO, TextIOWrapper

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for, current_app, send_from_directory
from flask_login import current_user
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from utils.decorators import role_required
from services.stats import get_admin_dashboard_stats, get_admin_report_stats
from services.export import students_csv_response, placement_report_csv_response
from services.eligibility import check_eligibility
from services.workflow import ALLOWED_APPLICATION_TRANSITIONS as WORKFLOW_TRANSITIONS, get_valid_next_statuses, is_valid_transition
from models import ActivityLog, Application, Company, PracticeQuestion, Resource, Student, User, PracticeAttempt, db


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
BRANCHES = ["CSE", "AIML", "IT", "ECE", "ME"]
STATUSES = ["Open", "Screening", "Interview", "Closed"]
APPLICATION_STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]
# Application status workflow: each key only permits its two direct next states.
ALLOWED_APPLICATION_TRANSITIONS = {
    status: list(get_valid_next_statuses(status))
    for status in APPLICATION_STATUSES
}


def log_activity(action, target):
    """Queue an audit entry in the current transaction for an admin mutation."""
    db.session.add(ActivityLog(
        admin_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        target=str(target)[:255],
    ))


@admin_bp.route("/profile", methods=["GET", "POST"])
@role_required("admin")
def profile():
    """Allow an admin to update account details and optionally change password."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        valid = True

        if len(name) < 2:
            flash("Name must be at least 2 characters.", "danger")
            valid = False
        if not email or "@" not in email or len(email) > 255:
            flash("Please enter a valid email address.", "danger")
            valid = False
        elif User.query.filter(User.email == email, User.id != current_user.id).first():
            flash("An account with this email already exists.", "danger")
            valid = False

        wants_password_change = any([current_password, new_password, confirm_password])
        if wants_password_change:
            if not check_password_hash(current_user.password_hash, current_password):
                flash("Current password is incorrect.", "danger")
                valid = False
            elif len(new_password) < 8:
                flash("New password must be at least 8 characters.", "danger")
                valid = False
            elif new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                valid = False

        if valid:
            current_user.name = name
            current_user.email = email
            if wants_password_change:
                current_user.password_hash = generate_password_hash(new_password)
            log_activity("update", f"Admin profile #{current_user.id} ({email})")
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("admin.profile"))

    return render_template("admin/profile.html", admin=current_user)


@admin_bp.route("/admins", methods=["GET", "POST"])
@role_required("admin")
def admins():
    """List and add administrator accounts; prevent unsafe removal."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("temporary_password", "")
        valid = True
        if len(name) < 2:
            flash("Admin name must be at least 2 characters.", "danger")
            valid = False
        if not email or "@" not in email or len(email) > 255:
            flash("Please enter a valid email address.", "danger")
            valid = False
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            valid = False
        if len(password) < 8:
            flash("Temporary password must be at least 8 characters.", "danger")
            valid = False
        if valid:
            admin_user = User(name=name, email=email, role="admin", password_hash=generate_password_hash(password))
            db.session.add(admin_user)
            log_activity("create", f"Admin account {email}")
            db.session.commit()
            flash(f"Administrator {email} created successfully.", "success")
            return redirect(url_for("admin.admins"))

    admin_users = User.query.filter_by(role="admin").order_by(User.name.asc()).all()
    return render_template("admin/admins.html", admins=admin_users)


@admin_bp.route("/admins/<int:admin_id>/delete", methods=["POST"])
@role_required("admin")
def delete_admin(admin_id):
    admin_user = db.session.get(User, admin_id)
    if admin_user is None or admin_user.role != "admin":
        flash("Administrator not found.", "danger")
        return redirect(url_for("admin.admins"))
    if admin_user.id == current_user.id:
        flash("You cannot remove your own administrator account.", "danger")
        return redirect(url_for("admin.admins"))
    admin_count = User.query.filter_by(role="admin").count()
    if admin_count <= 1:
        flash("The last administrator account cannot be removed.", "danger")
        return redirect(url_for("admin.admins"))

    email = admin_user.email
    log_activity("delete", f"Admin account {email}")
    db.session.delete(admin_user)
    db.session.commit()
    flash(f"Administrator {email} removed successfully.", "success")
    return redirect(url_for("admin.admins"))


@admin_bp.route("/activity")
@role_required("admin")
def activity():
    """Show the latest 50 administrator actions."""
    entries = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()
    return render_template("admin/activity.html", entries=entries)


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    """Build live placement metrics, charts, and recent application activity."""
    stats = get_admin_dashboard_stats()
    total_students = stats["total_students"]
    total_companies = stats["total_companies"]
    active_drives = stats["active_drives"]
    students_placed = stats["students_placed"]
    placement_percent = stats["placement_percent"]
    average_package = stats["average_package"]
    highest_package = stats["highest_package"]

    branch_names = ["CSE", "AIML", "IT", "ECE", "ME"]
    branch_labels = []
    branch_percentages = []
    for branch in branch_names:
        branch_total = Student.query.filter_by(branch=branch).count()
        branch_placed = (
            db.session.query(func.count(func.distinct(Application.student_id)))
            .join(Student, Application.student_id == Student.id)
            .filter(Student.branch == branch, Application.status == "Selected")
            .scalar()
            or 0
        )
        percentage = round((branch_placed / branch_total * 100), 1) if branch_total else 0
        branch_labels.append(branch)
        branch_percentages.append(percentage)

    companies = Company.query.order_by(Company.name.asc()).all()
    turnout_labels = []
    turnout_counts = []
    for company in companies:
        turnout_labels.append(company.name)
        turnout_counts.append(Application.query.filter_by(company_id=company.id).count())

    recent_activity = (
        Application.query.order_by(Application.updated_on.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        active_drives=active_drives,
        students_placed=students_placed,
        placement_percent=placement_percent,
        average_package=average_package,
        highest_package=highest_package,
        branch_labels=branch_labels,
        branch_percentages=branch_percentages,
        turnout_labels=turnout_labels,
        turnout_counts=turnout_counts,
        recent_activity=recent_activity,
    )


@admin_bp.route("/placement-report.csv")
@role_required("admin")
def export_placement_report():
    """Download the full placement application report for accreditation records."""
    applications = (
        Application.query.join(Student, Application.student_id == Student.id)
        .join(Company, Application.company_id == Company.id)
        .order_by(Student.roll_no.asc(), Company.name.asc())
        .all()
    )
    return placement_report_csv_response(applications)


@admin_bp.route("/reports")
@role_required("admin")
def reports():
    """Render placement analytics and accreditation summary tables."""
    report_stats = get_admin_report_stats()
    return render_template("admin/reports.html", report=report_stats)


def _filtered_students_query():
    """Build the admin student table query from persisted GET filter values."""
    branch = request.args.get("branch", "").strip()
    min_cgpa_text = request.args.get("min_cgpa", "").strip()
    placement = request.args.get("placed", "").strip().lower()
    search = request.args.get("search", "").strip()

    query = Student.query.join(User, Student.user_id == User.id)

    if branch in BRANCHES:
        query = query.filter(Student.branch == branch)
    if min_cgpa_text:
        try:
            min_cgpa = float(min_cgpa_text)
            if min_cgpa < 0:
                min_cgpa = 0
            query = query.filter(Student.cgpa >= min_cgpa)
        except (TypeError, ValueError):
            pass
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(User.name.ilike(pattern), Student.roll_no.ilike(pattern)))

    if placement in {"placed", "unplaced"}:
        placed_ids = db.session.query(Application.student_id).filter(Application.status == "Selected")
        if placement == "placed":
            query = query.filter(Student.id.in_(placed_ids))
        else:
            query = query.filter(~Student.id.in_(placed_ids))
    return query.order_by(Student.roll_no.asc())


@admin_bp.route("/students", methods=["GET"])
@role_required("admin")
def students():
    """List students with server-side branch, CGPA, placement, and text filters."""
    students_list = _filtered_students_query().all()
    return render_template(
        "admin/students.html",
        students=students_list,
        branches=BRANCHES,
        filters={
            "branch": request.args.get("branch", ""),
            "min_cgpa": request.args.get("min_cgpa", ""),
            "placed": request.args.get("placed", ""),
            "search": request.args.get("search", ""),
        },
    )


@admin_bp.route("/students/export.csv")
@role_required("admin")
def export_students_csv():
    """Download the currently filtered student table as a CSV report."""
    return students_csv_response(_filtered_students_query().all())


@admin_bp.route("/students/<int:student_id>", methods=["GET", "POST"])
@role_required("admin")
def student_detail(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    if request.method == "POST":
        cgpa_text = request.form.get("cgpa", "")
        backlogs_text = request.form.get("active_backlogs", "")
        valid = True
        try:
            cgpa = float(cgpa_text)
            if cgpa < 0 or cgpa > 10:
                flash("CGPA must be between 0 and 10.", "danger")
                valid = False
        except (TypeError, ValueError):
            flash("CGPA must be a valid number.", "danger")
            valid = False
        try:
            backlogs = int(backlogs_text)
            if backlogs < 0:
                flash("Active backlogs cannot be negative.", "danger")
                valid = False
        except (TypeError, ValueError):
            flash("Active backlogs must be a whole number.", "danger")
            valid = False

        if valid:
            student.cgpa = cgpa
            student.active_backlogs = backlogs
            log_activity("update", f"Student #{student.id} ({student.roll_no}) academics")
            db.session.commit()
            flash("Student academic details updated successfully.", "success")
            return redirect(url_for("admin.student_detail", student_id=student.id))

    applications = Application.query.filter_by(student_id=student.id).join(Company).order_by(Application.updated_on.desc()).all()
    attempts = PracticeAttempt.query.filter_by(student_id=student.id).order_by(PracticeAttempt.taken_on.desc()).all()
    return render_template(
        "admin/student_detail.html",
        student=student,
        applications=applications,
        attempts=attempts,
        application_statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@role_required("admin")
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    name = student.user.name
    roll_no = student.roll_no
    if student.resume_filename:
        resume_path = os.path.join(current_app.config["UPLOAD_FOLDER"], student.resume_filename)
        if os.path.isfile(resume_path):
            os.remove(resume_path)

    user = student.user
    log_activity("delete", f"Student #{student.id} ({roll_no})")
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash(f"Student '{name}' ({roll_no}) and related records were deleted.", "success")
    return redirect(url_for("admin.students"))


@admin_bp.route("/students/<int:student_id>/resume/<path:filename>")
@role_required("admin")
def download_student_resume(student_id, filename):
    student = db.session.get(Student, student_id)
    if student is None or student.resume_filename != filename:
        flash("Resume not found.", "danger")
        return redirect(url_for("admin.students"))
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@admin_bp.route("/companies")
@role_required("admin")
def companies():
    """List drives with applicant and eligibility totals computed live."""
    all_companies = Company.query.order_by(Company.drive_date.asc()).all()
    all_students = Student.query.all()
    eligible_counts = {}
    for company in all_companies:
        eligible_counts[company.id] = sum(
            1 for student in all_students
            if check_eligibility(student, company)[0]
        )
    return render_template(
        "admin/companies.html",
        companies=all_companies,
        eligible_counts=eligible_counts,
        statuses=STATUSES,
    )


@admin_bp.route("/companies/<int:company_id>/status", methods=["POST"])
@role_required("admin")
def update_company_status(company_id):
    """Quickly change a drive status from the company table."""
    company = db.session.get(Company, company_id)
    if company is None:
        flash("Company or drive not found.", "danger")
        return redirect(url_for("admin.companies"))

    new_status = request.form.get("status", "")
    if new_status not in STATUSES:
        flash("Please select a valid drive status.", "danger")
    elif new_status == company.status:
        flash(f"Drive is already {new_status}.", "info")
    else:
        company.status = new_status
        log_activity("update", f"Company #{company.id} {company.name} status to {new_status}")
        db.session.commit()
        flash(f"{company.name} status changed to {new_status}.", "success")
    return redirect(url_for("admin.companies"))


@admin_bp.route("/companies/<int:company_id>/eligible")
@role_required("admin")
def eligible_students(company_id):
    """Show eligible students and whether each student already applied."""
    company = db.session.get(Company, company_id)
    if company is None:
        flash("Company or drive not found.", "danger")
        return redirect(url_for("admin.companies"))

    eligible_students_list = []
    for student in Student.query.join(User, Student.user_id == User.id).order_by(User.name.asc()).all():
        is_eligible, _reason = check_eligibility(student, company)
        if is_eligible:
            applied = Application.query.filter_by(
                student_id=student.id,
                company_id=company.id,
            ).first() is not None
            eligible_students_list.append({"student": student, "applied": applied})

    return render_template(
        "admin/eligible_students.html",
        company=company,
        eligible_students=eligible_students_list,
    )


def validate_company_form():
    name = request.form.get("name", "").strip()
    role_title = request.form.get("role_title", "").strip()
    package_text = request.form.get("package_lpa", "")
    allowed_branches = request.form.getlist("allowed_branches")
    min_cgpa_text = request.form.get("min_cgpa", "")
    max_backlogs_text = request.form.get("max_backlogs", "")
    drive_date_text = request.form.get("drive_date", "")
    status = request.form.get("status", "")

    error = False
    if not name:
        flash("Company name is required.", "danger")
        error = True
    if not role_title:
        flash("Role title is required.", "danger")
        error = True

    try:
        package_lpa = float(package_text)
        if package_lpa <= 0:
            flash("Package must be greater than zero.", "danger")
            error = True
    except (TypeError, ValueError):
        flash("Package must be a valid number.", "danger")
        package_lpa = None
        error = True

    allowed_branches = [branch for branch in allowed_branches if branch in BRANCHES]
    if not allowed_branches:
        flash("Select at least one allowed branch.", "danger")
        error = True

    try:
        min_cgpa = float(min_cgpa_text)
        if min_cgpa < 0 or min_cgpa > 10:
            flash("Minimum CGPA must be between 0 and 10.", "danger")
            error = True
    except (TypeError, ValueError):
        flash("Minimum CGPA must be a valid number.", "danger")
        min_cgpa = None
        error = True

    try:
        max_backlogs = int(max_backlogs_text)
        if max_backlogs < 0:
            flash("Maximum backlogs cannot be negative.", "danger")
            error = True
    except (TypeError, ValueError):
        flash("Maximum backlogs must be a whole number.", "danger")
        max_backlogs = None
        error = True

    try:
        drive_date = datetime.strptime(drive_date_text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        flash("Please provide a valid drive date.", "danger")
        drive_date = None
        error = True

    if status not in STATUSES:
        flash("Please select a valid company status.", "danger")
        error = True

    data = None
    if not error:
        data = {
            "name": name,
            "role_title": role_title,
            "package_lpa": package_lpa,
            "allowed_branches": ",".join(allowed_branches),
            "min_cgpa": min_cgpa,
            "max_backlogs": max_backlogs,
            "drive_date": drive_date,
            "status": status,
        }
    return data


@admin_bp.route("/companies/new", methods=["GET", "POST"])
@role_required("admin")
def new_company():
    if request.method == "POST":
        data = validate_company_form()
        if data:
            company = Company(**data)
            db.session.add(company)
            db.session.flush()
            log_activity("create", f"Company #{company.id} {company.name}")
            db.session.commit()
            flash(f"Company '{company.name}' created successfully.", "success")
            return redirect(url_for("admin.companies"))

    return render_template("admin/company_form.html", company=None, branches=BRANCHES, statuses=STATUSES)


@admin_bp.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_company(company_id):
    company = db.session.get(Company, company_id)
    if company is None:
        flash("Company not found.", "danger")
        return redirect(url_for("admin.companies"))

    if request.method == "POST":
        data = validate_company_form()
        if data:
            for field, value in data.items():
                setattr(company, field, value)
            log_activity("update", f"Company #{company.id} {company.name}")
            db.session.commit()
            flash(f"Company '{company.name}' updated successfully.", "success")
            return redirect(url_for("admin.companies"))

    return render_template("admin/company_form.html", company=company, branches=BRANCHES, statuses=STATUSES)


@admin_bp.route("/companies/<int:company_id>/delete", methods=["POST"])
@role_required("admin")
def delete_company(company_id):
    company = db.session.get(Company, company_id)
    if company is None:
        flash("Company not found.", "danger")
        return redirect(url_for("admin.companies"))

    name = company.name
    log_activity("delete", f"Company #{company.id} {name}")
    db.session.delete(company)
    db.session.commit()
    flash(f"Company '{name}' and its applications were deleted.", "success")
    return redirect(url_for("admin.companies"))


@admin_bp.route("/applications", methods=["GET"])
@role_required("admin")
def applications():
    company_id = request.args.get("company_id", type=int)
    status = request.args.get("status", "").strip()
    branch = request.args.get("branch", "").strip()

    query = Application.query.join(Company, Application.company_id == Company.id).join(Student, Application.student_id == Student.id)
    if company_id:
        query = query.filter(Application.company_id == company_id)
    if status in APPLICATION_STATUSES:
        query = query.filter(Application.status == status)
    if branch in BRANCHES:
        query = query.filter(Student.branch == branch)

    all_applications = query.order_by(Application.updated_on.desc()).all()
    companies = Company.query.order_by(Company.name.asc()).all()
    return render_template(
        "admin/applications.html",
        applications=all_applications,
        companies=companies,
        statuses=APPLICATION_STATUSES,
        branches=BRANCHES,
        selected_company_id=company_id,
        selected_status=status,
        selected_branch=branch,
        allowed_transitions={status: get_valid_next_statuses(status) for status in APPLICATION_STATUSES},
    )


@admin_bp.route("/applications/<int:application_id>/status", methods=["POST"])
@role_required("admin")
def update_application_status(application_id):
    application = db.session.get(Application, application_id)
    if application is None:
        flash("Application not found.", "danger")
        return redirect(url_for("admin.applications"))

    new_status = request.form.get("status", "")
    allowed = get_valid_next_statuses(application.status)

    if application.status in {"Selected", "Rejected"}:
        flash(f"Application status is final: {application.status}.", "warning")
    elif not is_valid_transition(application.status, new_status):
        flash(
            f"Invalid status transition from {application.status} to {new_status}.",
            "danger",
        )
    else:
        application.status = new_status
        application.updated_on = datetime.utcnow()
        log_activity("update", f"Application #{application.id} status to {new_status}")
        db.session.commit()
        flash(f"Application status updated to {new_status}.", "success")

    return redirect(request.referrer or url_for("admin.applications"))


@admin_bp.route("/applications/bulk-status", methods=["POST"])
@role_required("admin")
def bulk_update_application_status():
    """Apply one target status only to rows whose workflow permits the transition."""
    target_status = request.form.get("target_status", "")
    application_ids = request.form.getlist("application_ids")

    if target_status not in APPLICATION_STATUSES:
        flash("Please choose a valid bulk status.", "danger")
        return redirect(request.referrer or url_for("admin.applications"))
    if not application_ids:
        flash("Select at least one application for the bulk action.", "warning")
        return redirect(request.referrer or url_for("admin.applications"))

    updated = 0
    skipped = 0
    now = datetime.utcnow()
    for raw_id in application_ids:
        try:
            application_id = int(raw_id)
        except (TypeError, ValueError):
            skipped += 1
            continue
        application = db.session.get(Application, application_id)
        if application is None or not is_valid_transition(application.status, target_status):
            skipped += 1
            continue
        application.status = target_status
        application.updated_on = now
        updated += 1

    if updated:
        log_activity("update", f"Bulk applications: {updated} rows status to {target_status}")
    db.session.commit()
    flash(
        f"Bulk update completed: {updated} application(s) updated; {skipped} skipped because their transitions were invalid or final.",
        "success" if updated else "warning",
    )
    return redirect(request.referrer or url_for("admin.applications"))


PREPARATION_CATEGORIES = ["Aptitude", "Coding", "Interview", "Resume"]


def validate_resource_link(link_or_text):
    """Allow plain text, but reject link-like values not using HTTP or HTTPS."""
    value = (link_or_text or "").strip().lower()
    if not value:
        return "Link or text is required."
    link_markers = value.startswith("www.") or "://" in value
    if link_markers and not value.startswith(("http://", "https://")):
        return "Links must start with http:// or https://."
    return None


@admin_bp.route("/resources", methods=["GET"])
@role_required("admin")
def resources():
    all_resources = Resource.query.order_by(Resource.added_on.desc()).all()
    return render_template("admin/resources.html", resources=all_resources, categories=PREPARATION_CATEGORIES)


@admin_bp.route("/resources/new", methods=["GET", "POST"])
@role_required("admin")
def new_resource():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "")
        link_or_text = request.form.get("link_or_text", "").strip()
        resource_error = validate_resource_link(link_or_text)
        if not title:
            flash("Title is required.", "danger")
        elif resource_error:
            flash(resource_error, "danger")
        elif category not in PREPARATION_CATEGORIES:
            flash("Please select a valid resource category.", "danger")
        else:
            resource = Resource(title=title, category=category, link_or_text=link_or_text, added_by=current_user.id)
            db.session.add(resource)
            db.session.flush()
            log_activity("create", f"Resource #{resource.id} {title}")
            db.session.commit()
            flash("Resource added successfully.", "success")
            return redirect(url_for("admin.resources"))
    return render_template("admin/resource_form.html", resource=None, categories=PREPARATION_CATEGORIES)


@admin_bp.route("/resources/<int:resource_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if resource is None:
        flash("Resource not found.", "danger")
        return redirect(url_for("admin.resources"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "")
        link_or_text = request.form.get("link_or_text", "").strip()
        resource_error = validate_resource_link(link_or_text)
        if not title:
            flash("Title is required.", "danger")
        elif resource_error:
            flash(resource_error, "danger")
        elif category not in PREPARATION_CATEGORIES:
            flash("Please select a valid resource category.", "danger")
        else:
            resource.title = title
            resource.category = category
            resource.link_or_text = link_or_text
            log_activity("update", f"Resource #{resource.id} {title}")
            db.session.commit()
            flash("Resource updated successfully.", "success")
            return redirect(url_for("admin.resources"))

    return render_template("admin/resource_form.html", resource=resource, categories=PREPARATION_CATEGORIES)


@admin_bp.route("/resources/<int:resource_id>/delete", methods=["POST"])
@role_required("admin")
def delete_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if resource is None:
        flash("Resource not found.", "danger")
    else:
        log_activity("delete", f"Resource #{resource.id} {resource.title}")
        db.session.delete(resource)
        db.session.commit()
        flash("Resource deleted successfully.", "success")
    return redirect(url_for("admin.resources"))


@admin_bp.route("/questions", methods=["GET"])
@role_required("admin")
def questions():
    category_filter = request.args.get("category", "").strip()
    question_query = PracticeQuestion.query
    if category_filter in PREPARATION_CATEGORIES:
        question_query = question_query.filter(PracticeQuestion.category == category_filter)
    all_questions = question_query.order_by(PracticeQuestion.category.asc(), PracticeQuestion.id.desc()).all()
    return render_template(
        "admin/questions.html",
        questions=all_questions,
        categories=PREPARATION_CATEGORIES,
        selected_category=category_filter,
    )


@admin_bp.route("/questions/new", methods=["GET", "POST"])
@role_required("admin")
def new_question():
    if request.method == "POST":
        category = request.form.get("category", "")
        question_text = request.form.get("question", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_option = request.form.get("correct_option", "").upper().strip()

        if category not in PREPARATION_CATEGORIES:
            flash("Please select a valid question category.", "danger")
        elif not all([question_text, option_a, option_b, option_c, option_d]):
            flash("Question and all four options are required.", "danger")
        elif correct_option not in {"A", "B", "C", "D"}:
            flash("Correct option must be A, B, C, or D.", "danger")
        else:
            question = PracticeQuestion(category=category, question=question_text, option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d, correct_option=correct_option)
            db.session.add(question)
            db.session.flush()
            log_activity("create", f"Question #{question.id}")
            db.session.commit()
            flash("Practice question added successfully.", "success")
            return redirect(url_for("admin.questions"))

    return render_template("admin/question_form.html", question=None, categories=PREPARATION_CATEGORIES)


@admin_bp.route("/questions/import", methods=["GET", "POST"])
@role_required("admin")
def import_questions():
    """Import practice questions from a validated CSV file."""
    if request.method == "POST":
        upload = request.files.get("csv_file")
        if upload is None or not upload.filename:
            flash("Please choose a CSV file to upload.", "danger")
            return redirect(url_for("admin.import_questions"))
        if not upload.filename.lower().endswith(".csv"):
            flash("Only CSV files can be imported.", "danger")
            return redirect(url_for("admin.import_questions"))

        imported = 0
        skipped = 0
        skipped_reasons = []
        try:
            stream = TextIOWrapper(upload.stream, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(stream)
            required = {"category", "question", "option_a", "option_b", "option_c", "option_d", "correct_option"}
            fieldnames = {name.strip().lower() for name in (reader.fieldnames or [])}
            missing_headers = sorted(required - fieldnames)
            if missing_headers:
                flash("CSV is missing required columns: " + ", ".join(missing_headers), "danger")
                return redirect(url_for("admin.import_questions"))

            for row_number, row in enumerate(reader, start=2):
                normalized = {str(key).strip().lower(): str(value).strip() if value is not None else "" for key, value in row.items()}
                category = normalized.get("category", "")
                question_text = normalized.get("question", "")
                options = [normalized.get(f"option_{letter}", "") for letter in ("a", "b", "c", "d")]
                correct = normalized.get("correct_option", "").upper()

                if category not in PREPARATION_CATEGORIES:
                    reason = "invalid category"
                elif not question_text:
                    reason = "question is empty"
                elif not all(options):
                    reason = "one or more options are empty"
                elif correct not in {"A", "B", "C", "D"}:
                    reason = "correct_option must be A, B, C, or D"
                else:
                    db.session.add(PracticeQuestion(category=category, question=question_text, option_a=options[0], option_b=options[1], option_c=options[2], option_d=options[3], correct_option=correct))
                    imported += 1
                    continue
                skipped += 1
                skipped_reasons.append(f"Row {row_number}: {reason}")
            if imported:
                log_activity("import", f"{imported} practice questions from CSV")
            db.session.commit()
        except (UnicodeDecodeError, csv.Error) as error:
            db.session.rollback()
            flash(f"Could not read the CSV file: {error}", "danger")
            return redirect(url_for("admin.import_questions"))

        flash(f"CSV import complete: {imported} imported and {skipped} skipped.", "success" if imported else "warning")
        for reason in skipped_reasons[:20]:
            flash(reason, "warning")
        if len(skipped_reasons) > 20:
            flash(f"{len(skipped_reasons) - 20} additional skipped-row reasons were omitted.", "warning")
        return redirect(url_for("admin.questions"))

    return render_template("admin/question_import.html", categories=PREPARATION_CATEGORIES)


@admin_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_question(question_id):
    question = db.session.get(PracticeQuestion, question_id)
    if question is None:
        flash("Question not found.", "danger")
        return redirect(url_for("admin.questions"))

    if request.method == "POST":
        category = request.form.get("category", "")
        question_text = request.form.get("question", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_option = request.form.get("correct_option", "").upper().strip()

        if category not in PREPARATION_CATEGORIES or correct_option not in {"A", "B", "C", "D"} or not all([question_text, option_a, option_b, option_c, option_d]):
            flash("Complete all question fields and select a valid category and correct option.", "danger")
        else:
            question.category = category
            question.question = question_text
            question.option_a = option_a
            question.option_b = option_b
            question.option_c = option_c
            question.option_d = option_d
            question.correct_option = correct_option
            log_activity("update", f"Question #{question.id}")
            db.session.commit()
            flash("Practice question updated successfully.", "success")
            return redirect(url_for("admin.questions"))

    return render_template("admin/question_form.html", question=question, categories=PREPARATION_CATEGORIES)


@admin_bp.route("/attempts", methods=["GET"])
@role_required("admin")
def attempts():
    """List practice attempts and average scores grouped by category."""
    all_attempts = (
        PracticeAttempt.query.join(Student, PracticeAttempt.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .order_by(PracticeAttempt.taken_on.desc())
        .all()
    )
    category_averages = (
        db.session.query(
            PracticeAttempt.category,
            func.avg(PracticeAttempt.score).label("average_score"),
            func.count(PracticeAttempt.id).label("attempt_count"),
        )
        .group_by(PracticeAttempt.category)
        .order_by(PracticeAttempt.category.asc())
        .all()
    )
    averages = [
        {
            "category": row.category or "General",
            "average_score": round(row.average_score or 0, 2),
            "attempt_count": row.attempt_count,
        }
        for row in category_averages
    ]
    return render_template("admin/attempts.html", attempts=all_attempts, averages=averages)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@role_required("admin")
def delete_question(question_id):
    question = db.session.get(PracticeQuestion, question_id)
    if question is None:
        flash("Question not found.", "danger")
    else:
        log_activity("delete", f"Question #{question.id}")
        db.session.delete(question)
        db.session.commit()
        flash("Practice question deleted successfully.", "success")
    return redirect(url_for("admin.questions"))
