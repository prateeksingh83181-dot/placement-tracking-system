from datetime import date, datetime

from werkzeug.security import generate_password_hash

from app import create_app
from models import (
    Application,
    Company,
    PracticeQuestion,
    Resource,
    Student,
    User,
    db,
)


app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    admin = User(
        name="College TPO Admin",
        email="admin@college.edu",
        password_hash=generate_password_hash("admin123"),
        role="admin",
    )
    db.session.add(admin)
    db.session.flush()

    resources = [
        Resource(title="Quantitative Aptitude Basics", category="Aptitude", link_or_text="https://www.indiabix.com/aptitude/questions-and-answers/", added_by=admin.id),
        Resource(title="Data Interpretation Guide", category="Aptitude", link_or_text="https://www.geeksforgeeks.org/data-interpretation/", added_by=admin.id),
        Resource(title="Python Coding Practice", category="Coding", link_or_text="https://www.hackerrank.com/domains/python", added_by=admin.id),
        Resource(title="DSA Interview Questions", category="Coding", link_or_text="https://www.geeksforgeeks.org/data-structures/", added_by=admin.id),
        Resource(title="SQL Practice Problems", category="Coding", link_or_text="https://leetcode.com/problemset/database/", added_by=admin.id),
        Resource(title="Common HR Interview Questions", category="Interview", link_or_text="https://www.themuse.com/advice/25-interview-questions-and-answers", added_by=admin.id),
        Resource(title="STAR Interview Method", category="Interview", link_or_text="Use Situation, Task, Action, and Result to structure behavioral answers.", added_by=admin.id),
        Resource(title="Resume Writing Checklist", category="Resume", link_or_text="Keep your resume concise, measurable, truthful, and tailored to the role.", added_by=admin.id),
        Resource(title="ATS-Friendly Resume Tips", category="Resume", link_or_text="Use keywords, standard headings, and simple formatting for applicant tracking systems.", added_by=admin.id),
        Resource(title="Placement Group Discussion Tips", category="Interview", link_or_text="https://www.careerizma.com/group-discussion-tips", added_by=admin.id),
    ]
    db.session.add_all(resources)

    student_data = [
        ("Aarav Sharma", "cse2026001@college.edu", "CSE24001", "CSE", 9.2, 0),
        ("Diya Patel", "aiml2026002@college.edu", "AIML24002", "AIML", 8.7, 0),
        ("Rohan Mehta", "it2026003@college.edu", "IT24003", "IT", 8.1, 1),
        ("Ananya Iyer", "ece2026004@college.edu", "ECE24004", "ECE", 7.8, 0),
        ("Kabir Singh", "me2026005@college.edu", "ME24005", "ME", 7.3, 2),
        ("Meera Nair", "cse2026006@college.edu", "CSE24006", "CSE", 8.9, 0),
        ("Arjun Rao", "aiml2026007@college.edu", "AIML24007", "AIML", 7.6, 1),
        ("Sara Khan", "it2026008@college.edu", "IT24008", "IT", 9.0, 0),
    ]

    students = []
    for name, email, roll_no, branch, cgpa, backlogs in student_data:
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash("student123"),
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
        students.append(student)

    companies = [
        Company(
            name="TechNova Solutions",
            role_title="Software Engineer",
            package_lpa=12.0,
            allowed_branches="CSE,AIML,IT",
            min_cgpa=8.0,
            max_backlogs=0,
            drive_date=date(2026, 11, 15),
            status="Open",
        ),
        Company(
            name="DataCore Analytics",
            role_title="Data Analyst",
            package_lpa=8.5,
            allowed_branches="CSE,AIML,IT,ECE",
            min_cgpa=7.5,
            max_backlogs=1,
            drive_date=date(2026, 11, 22),
            status="Screening",
        ),
        Company(
            name="CircuitWorks",
            role_title="Embedded Systems Engineer",
            package_lpa=7.8,
            allowed_branches="ECE,CSE",
            min_cgpa=7.0,
            max_backlogs=2,
            drive_date=date(2026, 12, 1),
            status="Interview",
        ),
        Company(
            name="MechEdge Industries",
            role_title="Graduate Engineer Trainee",
            package_lpa=6.5,
            allowed_branches="ME,ECE",
            min_cgpa=6.5,
            max_backlogs=2,
            drive_date=date(2026, 10, 20),
            status="Closed",
        ),
        Company(
            name="CloudPeak Systems",
            role_title="Cloud Associate",
            package_lpa=10.0,
            allowed_branches="CSE,AIML,IT",
            min_cgpa=7.8,
            max_backlogs=0,
            drive_date=date(2026, 12, 10),
            status="Open",
        ),
    ]
    db.session.add_all(companies)
    db.session.flush()

    question_data = [
        ("Aptitude", "What is 15% of 200?", "20", "25", "30", "35", "C"),
        ("Aptitude", "A train travels 60 km in 1 hour. How far will it travel in 2.5 hours at the same speed?", "120 km", "150 km", "180 km", "200 km", "B"),
        ("Aptitude", "What is the average of 10, 20, and 30?", "15", "20", "25", "30", "B"),
        ("Aptitude", "If 3x = 18, x equals:", "5", "6", "7", "8", "B"),
        ("Aptitude", "Which number is divisible by 3?", "122", "124", "126", "128", "C"),
        ("Aptitude", "A shop offers a 20% discount on 500 rupees. The discount is:", "80", "100", "120", "150", "B"),
        ("Aptitude", "What comes next: 2, 4, 8, 16, ?", "24", "30", "32", "34", "C"),
        ("Aptitude", "The ratio 2:3 is equivalent to:", "4:5", "6:9", "8:12", "10:12", "B"),
        ("Coding", "Which data structure uses FIFO?", "Stack", "Queue", "Tree", "Graph", "B"),
        ("Coding", "Which operation has average O(1) complexity in a hash table?", "Lookup", "Sorting", "Traversal", "Deletion of all entries", "A"),
        ("Coding", "What does SQL SELECT do?", "Updates data", "Deletes data", "Reads data", "Creates tables", "C"),
        ("Coding", "Which keyword creates a class in Python?", "def", "object", "class", "struct", "C"),
        ("Coding", "A binary search works on:", "Any list", "Sorted lists", "Unsorted trees only", "Hash tables only", "B"),
        ("Coding", "Which is NOT a stable sorting algorithm by default?", "Merge sort", "Insertion sort", "Bubble sort", "Quick sort", "D"),
        ("Coding", "What is time complexity of binary search?", "O(1)", "O(log n)", "O(n)", "O(n log n)", "B"),
        ("Coding", "Which SQL clause filters rows?", "GROUP BY", "WHERE", "ORDER BY", "JOIN", "B"),
        ("Interview", "What should you do first when asked a difficult interview question?", "Leave the interview", "Ask clarifying questions", "Guess immediately", "Change the topic", "B"),
        ("Interview", "The STAR method is commonly used for:", "Salary negotiation", "Behavioral questions", "Technical coding tests", "Company research", "B"),
        ("Interview", "Good body language includes:", "Avoiding eye contact", "Active posture and attentive listening", "Interrupting the interviewer", "Looking only at a phone", "B"),
        ("Interview", "What is the best response to asking about weaknesses?", "Claim you have none", "Give an honest weakness and improvement plan", "Criticize your team", "Avoid the question", "B"),
        ("Interview", "Why should you research a company before an interview?", "To memorize the logo", "To tailor answers and ask informed questions", "To skip technical preparation", "To negotiate without criteria", "B"),
        ("Interview", "What is a strong way to close an interview?", "Leave without speaking", "Summarize interest and ask next steps", "Demand an offer", "Critique the interviewer", "B"),
        ("Interview", "When describing a project, emphasize:", "Only its length", "Your role, actions, and results", "Only team failures", "Unrelated hobbies", "B"),
        ("Interview", "A thoughtful salary question should be based on:", "Market data and role responsibilities", "A random number", "The number of sick days", "Another employee's secret pay", "A"),
        ("Resume", "Which resume section highlights degree and institution?", "Education", "Hobbies", "References", "Photography", "A"),
        ("Resume", "Strong project bullets should include:", "Buzzwords only", "Actions and measurable results", "Full source code", "Personal secrets", "B"),
        ("Resume", "An ATS-friendly resume should use:", "Images for all headings", "Simple text and standard headings", "Multiple columns everywhere", "Unreadable fonts", "B"),
        ("Resume", "A resume should generally be:", "Unlimited in length", "Concise and relevant", "A list of every course", "Copied from a friend", "B"),
        ("Resume", "Project achievements are strongest when they:", "Use no numbers", "Include measurable impact", "Mention confidential data", "Are copied", "B"),
        ("Resume", "A resume should be updated when:", "Never", "Skills or achievements change", "Only after graduation", "An employee leaves", "B"),
    ]

    # Rebalance the seeded sample so each available Aptitude, Coding, and Interview
    # category contains the 10 questions required by the practice-test engine.
    for index in range(len(question_data) - 6, len(question_data)):
        row = list(question_data[index])
        row[0] = ["Aptitude", "Coding", "Interview"][index % 3]
        question_data[index] = tuple(row)

    db.session.add_all([
        PracticeQuestion(
            category=category,
            question=question,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
        )
        for category, question, option_a, option_b, option_c, option_d, correct_option in question_data
    ])

    applications = [
        Application(student=students[0], company=companies[0], status="Selected", applied_on=datetime(2026, 10, 2, 10, 0), updated_on=datetime(2026, 10, 20, 15, 30)),
        Application(student=students[1], company=companies[0], status="Shortlisted", applied_on=datetime(2026, 10, 3, 9, 15), updated_on=datetime(2026, 10, 21, 11, 0)),
        Application(student=students[2], company=companies[1], status="Interview", applied_on=datetime(2026, 10, 5, 14, 0), updated_on=datetime(2026, 10, 22, 16, 45)),
        Application(student=students[3], company=companies[2], status="Applied", applied_on=datetime(2026, 10, 8, 12, 30), updated_on=datetime(2026, 10, 8, 12, 30)),
        Application(student=students[4], company=companies[3], status="Rejected", applied_on=datetime(2026, 10, 1, 11, 0), updated_on=datetime(2026, 10, 18, 10, 0)),
        Application(student=students[5], company=companies[4], status="Shortlisted", applied_on=datetime(2026, 10, 9, 10, 20), updated_on=datetime(2026, 10, 23, 9, 30)),
        Application(student=students[7], company=companies[1], status="Selected", applied_on=datetime(2026, 10, 4, 13, 10), updated_on=datetime(2026, 10, 24, 14, 0)),
    ]
    db.session.add_all(applications)
    db.session.commit()

    print("Database reset and seeded successfully.")
