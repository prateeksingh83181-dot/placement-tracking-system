"""CSV export helpers for admin reports."""

import csv
from io import StringIO

from flask import Response

from models import Application


def students_csv_response(students):
    """Build a downloadable CSV response from a list of Student records."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Email", "Roll No", "Branch", "CGPA", "Active Backlogs",
        "Applications", "Placement Status", "Resume Filename",
    ])

    for student in students:
        placed = any(application.status == "Selected" for application in student.applications)
        writer.writerow([
            student.user.name,
            student.user.email,
            student.roll_no,
            student.branch,
            student.cgpa,
            student.active_backlogs,
            len(student.applications),
            "Placed" if placed else "Not placed",
            student.resume_filename or "",
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    return response


def placement_report_csv_response(applications):
    """Create an NAAC/NBA placement report for the supplied applications."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student", "Roll No", "Branch", "CGPA", "Company", "Role",
        "Package (LPA)", "Status", "Drive Date",
    ])
    for application in applications:
        student = application.student
        company = application.company
        writer.writerow([
            student.user.name,
            student.roll_no,
            student.branch,
            student.cgpa,
            company.name,
            company.role_title,
            company.package_lpa,
            application.status,
            company.drive_date.strftime("%Y-%m-%d"),
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=placement_report.csv"
    return response
