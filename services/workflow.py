"""Application status workflow rules and transition validation."""

ALLOWED_APPLICATION_TRANSITIONS = {
    "Applied": ("Shortlisted", "Rejected"),
    "Shortlisted": ("Interview", "Rejected"),
    "Interview": ("Selected", "Rejected"),
    "Selected": (),
    "Rejected": (),
}


def get_valid_next_statuses(current_status):
    """Return the statuses reachable directly from the current status."""
    return ALLOWED_APPLICATION_TRANSITIONS.get(current_status, ())


def is_valid_transition(current_status, new_status):
    """Return whether a workflow transition is permitted."""
    return new_status in get_valid_next_statuses(current_status)
