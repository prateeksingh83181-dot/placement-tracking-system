def check_eligibility(student, company):
    """Return the first failed eligibility rule, or the successful Eligible result.

    Checks deliberately run in the same priority used by the placement workflow:
    CGPA, branch, then active-backlog count.
    """
    # Eligibility is evaluated from current student and company database values.
    if student.cgpa < company.min_cgpa:
        return False, "CGPA below cut-off"

    allowed_branches = {
        branch.strip()
        for branch in (company.allowed_branches or "").split(",")
        if branch.strip()
    }
    if student.branch not in allowed_branches:
        return False, "Branch not allowed"

    if student.active_backlogs > company.max_backlogs:
        return False, "Backlog limit exceeded"

    return True, "Eligible"
