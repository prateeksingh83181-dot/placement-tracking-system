"""Live database statistics for the admin dashboard."""

from statistics import median

from sqlalchemy import func

from models import Application, Company, Student, db
from services.eligibility import check_eligibility


def get_admin_dashboard_stats():
    """Return core placement metrics computed from current database rows."""
    total_students = Student.query.count()
    total_companies = Company.query.count()
    active_drives = Company.query.filter(Company.status.in_(["Open", "Screening", "Interview"])).count()

    placed_student_ids = (
        db.session.query(Application.student_id)
        .filter(Application.status == "Selected")
        .distinct()
        .all()
    )
    students_placed = len({row.student_id for row in placed_student_ids})
    placement_percent = round(students_placed / total_students * 100, 1) if total_students else 0.0

    package_by_student = {}
    selected_applications = (
        Application.query.filter_by(status="Selected")
        .join(Company, Application.company_id == Company.id)
        .all()
    )
    for application in selected_applications:
        package_by_student[application.student_id] = max(
            application.company.package_lpa,
            package_by_student.get(application.student_id, 0),
        )

    packages = list(package_by_student.values())
    average_package = round(sum(packages) / len(packages), 2) if packages else 0.0
    highest_package = max(packages) if packages else 0.0

    return {
        "total_students": total_students,
        "total_companies": total_companies,
        "active_drives": active_drives,
        "students_placed": students_placed,
        "placement_percent": placement_percent,
        "average_package": average_package,
        "highest_package": highest_package,
    }


def get_admin_report_stats():
    """Compute chart datasets and accreditation summary tables for admin reports."""
    branches = ["CSE", "AIML", "IT", "ECE", "ME"]
    students = Student.query.all()
    companies = Company.query.order_by(Company.name.asc()).all()

    branch_labels = []
    branch_placement_percentages = []
    branch_summary = []
    for branch in branches:
        branch_students = [student for student in students if student.branch == branch]
        total = len(branch_students)
        placed_ids = {
            application.student_id
            for application in Application.query.filter(Application.status == "Selected").all()
            if application.student_id in {student.id for student in branch_students}
        }
        placed = len(placed_ids)
        placement_percent = round(placed / total * 100, 1) if total else 0.0

        eligible_count = sum(
            1 for student in branch_students
            if any(check_eligibility(student, company)[0] for company in companies)
        )
        applied_count = len({
            application.student_id
            for student in branch_students
            for application in student.applications
        })
        selected_packages = [
            application.company.package_lpa
            for student in branch_students
            for application in student.applications
            if application.status == "Selected"
        ]
        average_package = round(sum(selected_packages) / len(selected_packages), 2) if selected_packages else 0.0

        branch_labels.append(branch)
        branch_placement_percentages.append(placement_percent)
        branch_summary.append({
            "branch": branch,
            "total_students": total,
            "eligible_count": eligible_count,
            "applied_count": applied_count,
            "placed_count": placed,
            "placement_percent": placement_percent,
            "average_package": average_package,
        })

    turnout_labels = [company.name for company in companies]
    turnout_counts = [len(company.applications) for company in companies]

    status_counts = {}
    for status in ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]:
        status_counts[status] = Application.query.filter_by(status=status).count()

    selected_applications = Application.query.filter_by(status="Selected").join(Company).all()
    offer_packages = [application.company.package_lpa for application in selected_applications]
    package_stats = {
        "average": round(sum(offer_packages) / len(offer_packages), 2) if offer_packages else 0.0,
        "highest": max(offer_packages) if offer_packages else 0.0,
        "lowest": min(offer_packages) if offer_packages else 0.0,
        "median": round(float(median(offer_packages)), 2) if offer_packages else 0.0,
        "total_offers": len(selected_applications),
    }

    return {
        "branch_labels": branch_labels,
        "branch_placement_percentages": branch_placement_percentages,
        "turnout_labels": turnout_labels,
        "turnout_counts": turnout_counts,
        "status_labels": list(status_counts.keys()),
        "status_counts": list(status_counts.values()),
        "package_stats": package_stats,
        "branch_summary": branch_summary,
    }
