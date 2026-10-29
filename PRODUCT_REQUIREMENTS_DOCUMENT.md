# Placement Preparation & Tracking System

## Product Requirements Document (PRD)

**Product:** Placement Preparation & Tracking System  
**Document version:** 1.0  
**Platform:** Web application  
**Technology stack:** Python 3, Flask, Flask-SQLAlchemy, SQLite, Flask-Login, Jinja2, Bootstrap 5 CDN, Chart.js CDN  
**Primary users:** College students and Training & Placement Officers (TPOs/admins)  
**Document status:** Implemented product specification

---

## 1. Executive Summary

The Placement Preparation & Tracking System is a centralized web platform for managing a college placement lifecycle. It supports student registration and profiles, resume uploads, company drive administration, eligibility-based applications, application-status workflows, interview preparation, practice tests, placement analytics, CSV reporting, and administrative auditing.

The system must provide students with a clear view of placement opportunities and preparation resources while enabling TPOs to manage drives, monitor applicant pipelines, control access, update student outcomes, and produce accreditation-ready placement reports.

## 2. Product Goals

1. Centralize student, company, application, preparation, and placement data.
2. Reduce manual eligibility verification and application tracking.
3. Give students an accurate, real-time view of eligible drives and application status.
4. Give administrators a complete operational and analytical view of placement activity.
5. Enforce role-based authorization and valid placement-status transitions.
6. Provide exportable records suitable for NAAC/NBA reporting.
7. Ensure the application works as a simple local or institutional Flask deployment.

## 3. Success Metrics

- **Student adoption:** Percentage of enrolled students completing registration and at least one profile update.
- **Drive coverage:** Percentage of active drives with accurate eligibility criteria.
- **Application usage:** Number and percentage of eligible students who apply for suitable drives.
- **Placement progress:** Students placed divided by total students.
- **Branch performance:** Selected students divided by total students within each branch.
- **Turnout:** Applications received per company drive.
- **Preparation engagement:** Number of practice tests started and completed.
- **Reporting readiness:** Percentage of selected placement records available through placement CSV exports.

## 4. Users and Personas

### 4.1 Student

A student seeking placement opportunities, managing profile and resume information, viewing eligible drives, applying for companies, tracking selection progress, using preparation resources, and taking practice tests.

**Student objectives:**

- Register and maintain accurate academic data.
- Upload a current PDF resume.
- Find drives for which the student qualifies.
- Avoid duplicate applications.
- Track application progression transparently.
- Improve readiness through resources and tests.

### 4.2 TPO/Admin

A placement-cell administrator responsible for maintaining company drives, student records, application statuses, preparation content, reports, users, and audit logs.

**Admin objectives:**

- Maintain accurate placement data.
- Manage company eligibility criteria and statuses.
- Review the complete applicant pipeline.
- Select valid status transitions and prevent invalid changes.
- Identify student eligibility and placement gaps.
- Export institutional reports.
- Maintain controlled administrator access.

## 5. Scope

### 5.1 In Scope

- Landing page and authentication.
- Student registration, login, logout, profile, resume upload, dashboard, applications, resources, and practice tests.
- Admin dashboard, student management, company management, application management, preparation management, reports, profile, admin users, and activity logs.
- Server-side role authorization and form validation.
- Live SQLite-backed placement statistics.
- Chart.js visualizations.
- Student, placement, and question CSV workflows.
- Seed data for demonstration and testing.
- Responsive Bootstrap 5 layout.

### 5.2 Out of Scope for the Current Release

- Email/SMS notifications.
- External identity providers such as OAuth or SSO.
- Cloud object storage for resumes.
- Automated resume parsing.
- Online proctoring.
- Native mobile applications.
- Multi-college tenancy.
- Event scheduling or interview calendars.
- Advanced applicant ranking or AI-based candidate recommendations.
- Production-grade background job processing.
- Two-factor authentication.

## 6. User Roles and Permissions

| Capability | Student | Admin |
|---|---:|---:|
| Register and log in | Yes | Yes if seeded/created |
| View student profile | Own profile | Any student |
| Edit academic details | CGPA/backlogs/email/resume | Any student's CGPA/backlogs |
| View eligible drives | Yes | Yes |
| Apply for eligible open drives | Yes | No |
| View own applications | Yes | Yes, along with all applications |
| Manage companies/drives | No | Yes |
| Transition application statuses | No | Yes, under workflow rules |
| Manage preparation resources/questions | No | Yes |
| View reports and analytics | No | Yes |
| Manage admin users | No | Yes, with self/last-admin safeguards |
| View audit activity | No | Yes |

### Authorization Rules

- Unauthenticated users can access public landing, login, and registration routes.
- `/student/*` routes require the `student` role.
- `/admin/*` routes require the `admin` role.
- A student accessing an admin route receives HTTP 403.
- An administrator accessing a student-only route receives HTTP 403.
- Unknown routes return a custom HTTP 404 page.

## 7. Functional Requirements

### 7.1 Authentication and Account Management

#### Student Registration

The registration form accepts:

- Name
- Email
- Roll number
- Branch
- CGPA
- Active backlogs
- Password
- Confirm password

Validation requirements:

- Name and roll number must not be empty.
- Email must be valid, normalized, and unique.
- Roll number must be unique.
- Branch must be one of CSE, AIML, IT, ECE, or ME.
- CGPA must be numeric and between 0 and 10 inclusive.
- Active backlogs must be a non-negative integer.
- Password and confirmation password must match.
- The system creates a corresponding User and Student record.

#### Login

- A single login page accepts email and password.
- Passwords are checked against Werkzeug password hashes.
- A student redirects to `/student/dashboard`.
- An administrator redirects to `/admin/dashboard`.
- Invalid credentials display a flash error.

#### Logout

- Authenticated users can end the session from the navbar.
- Logout redirects to the login or landing experience.

#### Admin Profile

Administrators can update:

- Name
- Email
- Password, requiring the current password

New passwords require confirmation and a minimum length of 8 characters. Email uniqueness and valid account data must be enforced server-side.

#### Administrator Management

- Admins can list all admin accounts.
- Admins can create a new admin account with a name, unique email, and temporary password.
- Admins cannot remove themselves.
- The system prevents removal of the final administrator.
- Removal is confirmed through the destructive-action confirmation mechanism.

### 7.2 Student Profile

The profile page displays:

- Name
- Email
- Roll number
- Branch
- CGPA
- Active backlogs
- Current resume, where available

Editable fields:

- Email
- CGPA
- Active backlogs

Resume requirements:

- PDF format only, validated by extension/MIME where available.
- Maximum 2 MB.
- Filename uses the student's roll number and a sanitized filename.
- Uploading a replacement removes the previous resume file.
- Student resumes are downloadable through a protected route.
- Deleting a student removes its resume file and related records.

### 7.3 Student Dashboard

The dashboard displays:

- Current CGPA
- Current active backlogs
- Number of drives for which the student is eligible
- Number of applications submitted

Each company with status `Open` is displayed as a card containing:

- Company name
- Role title
- Package
- CGPA cutoff
- Allowed branches
- Maximum backlogs
- Drive date
- Application/eligibility tag

The card state must be one of:

- **Eligible:** Green Eligible badge and Apply button.
- **Applied:** Blue Applied badge and no duplicate Apply button.
- **Not eligible:** Red reason badge and no Apply button.

### 7.4 Eligibility Engine

Eligibility is calculated on live database values. Checks run in this order:

1. CGPA must meet or exceed `min_cgpa`.
2. Student branch must exist in the company's comma-separated allowed branches.
3. Active backlogs must be less than or equal to `max_backlogs`.

Result rules:

- If CGPA fails: `CGPA below cut-off`
- If branch fails: `Branch not allowed`
- If backlog count fails: `Backlog limit exceeded`
- If all checks pass: `Eligible`

The eligibility function must return:

```text
(is_eligible, reason)
```

Before an application is created, the server must:

- Verify the student exists.
- Recheck eligibility.
- Confirm the company exists.
- Confirm the student has not already applied.
- Create a unique application in `Applied` status.

### 7.5 Student Applications

Each application shows:

- Company name
- Role title where displayed
- Applied timestamp
- Last updated timestamp
- Current status

The application pipeline is displayed horizontally:

```text
Applied → Shortlisted → Interview → Selected
```

Special handling:

- Completed stages are green.
- The current stage is highlighted.
- A rejected application is displayed in red.
- Selected and Rejected are final states.

### 7.6 Company and Drive Management

Administrators can view, create, edit, and delete drives.

Drive fields:

- Company name
- Role title
- Package in LPA
- Allowed branches
- Minimum CGPA
- Maximum backlogs
- Drive date
- Status

Validation:

- Name, role, and drive date are required.
- Package must be greater than 0.
- CGPA must be between 0 and 10.
- Maximum backlogs must be non-negative.
- At least one branch must be selected.
- Status must be Open, Screening, Interview, or Closed.

Company status order:

```text
Open → Screening → Interview → Closed
```

Status changes can be made through a dropdown in the table. For operational purposes, any valid status in the company status domain is selectable, without inventing an application transition.

Deleting a company:

- Must require confirmation.
- Deletes all applications associated with that company.
- Displays an action-result flash message.

The companies table shows:

- Package, cutoff, backlogs, branches, date, status
- Applicant count
- Eligible student count
- Eligible-student view
- Edit and delete actions

### 7.7 Application Administration

The applications table shows:

- Student name, roll number, branch, and CGPA
- Company and role
- Current status
- Applied timestamp
- Updated timestamp

Filters:

- Company
- Application status
- Branch

Filters operate through GET parameters and remain visible in the controls.

#### Single-Row Status Updates

Dropdown options must contain only valid next states:

| Current | Valid Next States |
|---|---|
| Applied | Shortlisted, Rejected |
| Shortlisted | Interview, Rejected |
| Interview | Selected, Rejected |
| Selected | None |
| Rejected | None |

Every update sets `updated_on` to the current timestamp.

#### Bulk Status Updates

- Rows are selectable by checkbox.
- Supported bulk target statuses are Shortlisted, Interview, Selected, and Rejected.
- Only valid transitions are applied.
- Invalid and final-state rows are skipped.
- The admin receives a count of updated and skipped applications.

### 7.8 Student Administration

The student list includes:

- Name
- Roll number
- Branch
- CGPA
- Active backlogs
- Number of applications
- Placement status: Placed or Not placed
- Resume link where available

Filters:

- Branch
- Minimum CGPA
- Placed/unplaced
- Name or roll-number search

GET parameters preserve filter values.

Student detail includes:

- Full profile
- Resume download
- All applications and status pipeline
- All practice attempts

An administrator may:

- Edit CGPA and active backlogs with validation.
- Delete a student, which cascades to applications and practice attempts.
- Export filtered student results to CSV.

Deleting a student requires confirmation and removes the associated User record according to cascades.

### 7.9 Preparation Resources

Resource fields:

- Title
- Category: Aptitude, Coding, Interview, or Resume
- Link or text content
- Added-by administrator
- Added-on timestamp

Resource validation:

- Title is required.
- Category is restricted to supported values.
- If a value is intended as a link, it must start with `http://` or `https://`.

Admin CRUD operations include add, edit, and delete. Delete requires confirmation.

Student preparation pages group resources by category and offer a practice test entry point.

### 7.10 Practice Questions

Question fields:

- Category
- Question text
- Option A
- Option B
- Option C
- Option D
- Correct option

Validation:

- Category belongs to Aptitude, Coding, Interview, or Resume.
- Question text and four options are required and non-empty.
- Correct option is exactly A, B, C, or D.

Admin features include:

- Add/edit/delete questions
- Filter questions by category
- CSV import

CSV import must accept:

```text
category,question,option_a,option_b,option_c,option_d,correct_option
```

Import behavior:

- Validate every row independently.
- Count successfully imported rows.
- Count skipped rows and report an immediate reason for failures.
- Reject invalid category values and answer letters.
- Reject empty required fields.

### 7.11 Practice Tests

A practice test selects up to 10 random MCQs for a selected category.

Test behavior:

- The student chooses Aptitude, Coding, Interview, or Resume.
- Questions are randomized.
- The student submits option selections.
- Results show score, total, correct answers, and selected/correct-answer context.
- The attempt is saved with student, category, score, total, and timestamp.
- Past attempts are visible on the student preparation page.

If fewer than 10 questions are available, the test uses all available questions in that category.

### 7.12 Practice Attempt Administration

The admin attempts page includes:

- Student name
- Category
- Score/total
- Attempt date/time
- Average scores grouped by category
- Attempt counts grouped by category

### 7.13 Admin Dashboard

Live metrics:

- Total students
- Total companies
- Active drives: Open, Screening, or Interview
- Students placed by distinct `Selected` applications
- Overall placement percentage
- Average package of selected students
- Highest package

Recent activity displays the 10 most recently updated applications with:

- Student name
- Company
- Status badge
- Time

### 7.14 Reports and Analytics

The report page provides:

#### Charts

1. Branch-wise placement percentage.
2. Company/drive-wise applicant turnout.
3. Application-status distribution.

All chart values are passed from Flask as JSON and rendered by Chart.js.

#### Package Statistics

- Average selected package
- Highest selected package
- Lowest selected package
- Median selected package
- Total offers/selected applications

Package calculations use selected applications and company package values.

#### Branch Summary

For CSE, AIML, IT, ECE, and ME:

- Total students
- Students eligible for at least one drive
- Students with at least one application
- Students placed
- Placement percentage
- Average package

#### Placement CSV Export

The placement export includes:

- Student name
- Roll number
- Branch
- CGPA
- Company
- Role
- Package
- Status
- Drive date

The export is suitable for internal NAAC/NBA-style records.

### 7.15 Audit Trail

Administrators' mutations are recorded in `ActivityLog` records containing:

- Administrator ID where available
- Action
- Target
- Timestamp

The activity page shows the latest 50 entries in descending timestamp order.

Mutations should be logged for at least:

- Create, update, and delete of companies
- Create, update, and delete of resources and questions
- Student academic updates/deletions
- Application status and bulk status updates
- Admin account and profile operations
- Question imports

Every destructive action should have a JavaScript confirmation dialog and server-side authorization.

## 8. Status Models

### 8.1 Drive Status

```text
Open
Screening
Interview
Closed
```

### 8.2 Application Status

```text
Applied → Shortlisted → Interview → Selected
                         ↘
                         Rejected
```

From Shortlisted, the valid terminal rejection path also exists:

```text
Shortlisted → Rejected
```

### 8.3 Badge Colours

The following consistent colors are used:

| Status | Badge |
|---|---|
| Open | Green |
| Screening | Yellow |
| Interview | Blue |
| Closed | Grey |
| Applied | Secondary/Grey |
| Shortlisted | Info/Cyan |
| Interview | Primary/Blue |
| Selected | Success/Green |
| Rejected | Danger/Red |

## 9. Data Model

### 9.1 User

- `id`: integer primary key
- `name`: string, required
- `email`: unique string, required
- `password_hash`: string, required
- `role`: student or admin

### 9.2 Student

- `id`: integer primary key
- `user_id`: unique foreign key to User
- `roll_no`: unique string
- `branch`: CSE, AIML, IT, ECE, or ME
- `cgpa`: float
- `active_backlogs`: integer
- `resume_filename`: nullable string

Relationships:

- One Student belongs to one User.
- One Student has many Applications.
- One Student has many PracticeAttempts.

### 9.3 Company

- `id`: integer primary key
- `name`: string
- `role_title`: string
- `package_lpa`: float
- `allowed_branches`: comma-separated string
- `min_cgpa`: float
- `max_backlogs`: integer
- `drive_date`: date
- `status`: drive status

One Company has many Applications.

### 9.4 Application

- `id`: integer primary key
- `student_id`: foreign key
- `company_id`: foreign key
- `status`: application status
- `applied_on`: datetime
- `updated_on`: datetime

Database constraints:

- Unique combination of student and company.
- Application status constrained to the five supported values.

### 9.5 Resource

- `id`: integer primary key
- `title`
- `category`
- `link_or_text`
- `added_by`: foreign key to User
- `added_on`

### 9.6 PracticeQuestion

- `id`: integer primary key
- `category`
- `question`
- `option_a`
- `option_b`
- `option_c`
- `option_d`
- `correct_option`: A, B, C, or D

### 9.7 PracticeAttempt

- `id`: integer primary key
- `student_id`: foreign key
- `category`
- `score`
- `total`
- `taken_on`

### 9.8 ActivityLog

- `id`: integer primary key
- `admin_id`: nullable foreign key
- `action`
- `target`
- `timestamp`

## 10. System Architecture

### 10.1 Application Structure

```text
placement_system/
├── app.py                 # Flask app factory, extensions, DB setup, error handlers
├── config.py              # Secret and SQLite/upload configuration
├── models.py              # SQLAlchemy models and relationships
├── seed.py                # Seed/reset utility
├── routes/
│   ├── auth.py            # Authentication routes
│   ├── student.py         # Student routes
│   └── admin.py           # Administrator routes
├── services/
│   ├── eligibility.py     # Eligibility engine
│   ├── workflow.py        # Application transition rules
│   ├── stats.py           # Dashboard/report calculations
│   └── export.py          # CSV response generation
├── utils/
│   └── decorators.py      # Role-based route protection
├── templates/
│   ├── base.html
│   ├── student/
│   └── admin/
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
└── requirements.txt
```

### 10.2 Request Flow

1. Flask receives the route request.
2. Flask-Login restores the authenticated user where required.
3. The role decorator verifies the user's role.
4. The route validates all request values.
5. Services calculate eligibility, workflow validity, statistics, or exports.
6. SQLAlchemy reads or modifies SQLite records.
7. Flash messages communicate success or validation errors.
8. Jinja2 renders the response with consistent Bootstrap components.

### 10.3 Database Initialization

- Flask-SQLAlchemy is configured with SQLite.
- `db.create_all()` initializes missing tables.
- The app performs lightweight compatibility handling for existing databases when needed.
- `seed.py` resets all seedable records and inserts demonstration data.

## 11. User Interface Requirements

- All functional pages extend the shared base layout.
- The navbar identifies the authenticated user name and role.
- Students receive student navigation links.
- Administrators receive the admin panel shell and profile access.
- Tables are horizontally responsive.
- Forms use Bootstrap controls and clear labels.
- Flash messages are categorized and dismissible.
- Destructive actions use confirmation dialogs.
- Empty states explain that no records exist and provide a relevant add action.
- Admin sidebar collapses into wrapped/top-menu behavior on mobile widths.
- Status colors remain consistent across all pages.
- Charts load through Bootstrap-compatible Chart.js markup.

## 12. Validation and Error Handling

The UI is not trusted as the validation boundary. Every mutation route validates:

- Required fields
- Numeric ranges
- Email uniqueness
- Integer values
- Allowed enums and branches
- Application transition validity
- File extension and size
- Password confirmation
- Duplicate applications

Expected flash categories:

- Success for completed actions.
- Danger for invalid input or unauthorized operation.
- Warning for partial bulk actions or skipped rows.
- Info for neutral state changes.

Custom pages:

- 403 for role mismatch/forbidden access.
- 404 for missing routes/resources.
- 413 for uploads larger than the configured limit.

## 13. Security Requirements

- Passwords must be stored only as Werkzeug password hashes.
- The Flask secret key must not be committed as a real production secret.
- Production deployments must run under environment-specific configuration.
- Role checks must be applied in route decorators, not only hidden UI elements.
- Current user objects must always be fetched through Flask-Login.
- Uploaded filenames must use `secure_filename` and student-safe prefixes.
- Resume downloads must not expose arbitrary files outside the upload directory.
- SQLite database, uploads, environment files, and Python caches must not be committed.
- CSRF protection should be added before internet-facing production deployment; the current application relies on same-session POST action validation unless framework-level protection is introduced.
- Destructive POST routes must not be callable through role-free GET routes.

## 14. Non-Functional Requirements

### Reliability

- Database writes are committed only after successful validation.
- Deleting parent records cascades to dependent records where relationships require it.
- Bulk operations report partial success explicitly.

### Performance

- Analytical queries are suitable for a small-to-medium college dataset.
- Files are stored locally under `static/uploads`.
- Candidate eligibility is calculated only for the relevant student/company set.

### Usability

- Primary workflows require limited navigation.
- Status and package data are visually distinguishable.
- Mobile users can access all primary administrative pages.

### Maintainability

- Domain rules are separated into service modules.
- Models and routes use Flask-SQLAlchemy conventions.
- Reusable badge and admin layouts reduce template duplication.
- Seed logic should remain separate from application startup in production.

### Portability

- The application requires Python 3 and pip.
- SQLite requires no external database server.
- Bootstrap and Chart.js are loaded through CDN and require internet access for those assets.

## 15. Seed Data Requirements

`seed.py` resets demonstration data and seeds:

- One administrator account
- Eight students across CSE, AIML, IT, ECE, and ME
- Five companies with varied packages, cutoff values, statuses, and branch criteria
- Sample applications across the application status pipeline
- Ten resources across the four resource categories
- Thirty practice questions across the four question categories

Default accounts:

| Role | Email | Password |
|---|---|---|
| Admin/TPO | `admin@college.edu` | `admin123` |
| Student example | `cse2026001@college.edu` | `student123` |

Running the seed utility is destructive for existing seeded database data and should not be used in production without review.

## 16. Setup and Operations

### Installation

```bash
cd placement_system
pip install -r requirements.txt
python seed.py
python app.py
```

### Default URL

```text
http://127.0.0.1:5000/
```

### Database

SQLite is stored at `placement.db` by the application configuration. The upload folder is under `static/uploads`.

### Development Notes

- Run seed only after intending to reset demonstration data.
- Debug mode is appropriate for local development only.
- Use an environment variable or secure deployment configuration for the production secret key.
- Resume directories and generated database files must be backed up separately from source code.

## 17. Acceptance Criteria

### Authentication

- Student can register with unique credentials.
- Student can log in and reach the student dashboard.
- Admin can log in and reach the admin dashboard.
- Student cannot access admin routes and receives 403.
- Admin cannot access student-only routes and receives 403.
- Logout ends the session.

### Eligibility and Applications

- Company cards display the correct Eligible/Applied/Not eligible state.
- Eligibility fails in CGPA, branch, and backlog priority order.
- Duplicate applications are rejected.
- Ineligible students cannot apply through direct POST requests.
- Student pipeline reflects the database status immediately.

### Admin Management

- All admin tables show seeded records and handle empty states cleanly.
- Company validation prevents invalid package, CGPA, branch, and status values.
- Application transitions obey the workflow rules.
- Bulk actions update only valid rows and report skipped rows.
- Student deletion cascades safely to applications and attempts.
- CSV exports contain expected headers and values.

### Preparation

- Resources are grouped correctly for students.
- Practice tests save attempts and show answer review.
- Admin question import reports imported and skipped counts.
- Invalid question content is not persisted.

### Reporting

- Dashboard metrics match live database values.
- Branch and drive charts render valid JSON-backed data.
- Package and branch summary statistics contain no divide-by-zero errors.
- Placement export downloads successfully.

### Admin Safety

- Admin profile validation works.
- Last admin cannot be removed.
- Self-removal is blocked.
- Activity page displays latest actions.
- All delete actions show confirmation behavior.

## 18. Release Checklist

- Install dependencies from `requirements.txt` on a clean Python environment.
- Compile all Python modules.
- Create an isolated SQLite database through `db.create_all()` or seed.
- Verify public and role-protected routes.
- Verify custom 403 and 404 pages.
- Verify registration and login credentials.
- Verify resume upload, replacement, download, and deletion.
- Verify every application workflow transition.
- Verify bulk application updates.
- Verify company, student, resource, and question CRUD operations.
- Verify CSV imports and exports.
- Verify Chart.js and responsive layouts.
- Verify no database or uploaded user files are committed.
- Change the development secret key in any real deployment.
- Add production CSRF protection before deployment to an untrusted network.

## 19. Future Enhancements

1. Email notifications for shortlist, interview, and selection updates.
2. Interview scheduling and calendar integrations.
3. Student document vault for academic certificates and additional resumes.
4. Recruiter portal and externally controlled company accounts.
5. Automated application deadline handling.
6. AI-assisted resume feedback and skill-gap recommendations.
7. Time-limited, category-based mock tests with configurable question counts.
8. Pagination, full-text search, and server-side table filtering.
9. PostgreSQL/MySQL support for multi-institution deployment.
10. Cloud/object storage for resumes.
11. Two-factor authentication and password-reset workflow.
12. Cross-site request forgery protection and content security policy.
13. Background job processing for bulk exports and notifications.
14. Multi-year placement analytics and cohort comparisons.
15. Docker deployment and automated CI/CD pipelines.
16. Formal role permissions beyond the current student/admin split.

## 20. Glossary

- **CGPA:** Student cumulative grade point average.
- **Active backlog:** A current academic subject/paper not yet cleared.
- **Drive:** A company recruitment event managed in the placement system.
- **TPO:** Training & Placement Officer.
- **Eligible student:** A student satisfying CGPA, branch, and backlog conditions.
- **Application pipeline:** The sequence of statuses from Applied to Selected or Rejection.
- **Placement offer:** A selected application with an associated company package.
- **NAAC/NBA:** Indian accreditation frameworks that may consume placement evidence and reports.
- **Activity log:** Administrative action audit trail stored in SQLite.
