from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(role):
    """Restrict a view to authenticated users with the requested role."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
