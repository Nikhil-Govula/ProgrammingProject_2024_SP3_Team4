from functools import wraps
from flask import g, redirect, url_for

def auth_required(f=None, user_type=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                print(f"No user in session, redirecting to landing")  # Debug log
                return redirect(url_for('landing.landing'))
            if user_type and g.user_type != user_type:
                print(f"User type mismatch. Expected: {user_type}, Got: {g.user_type}")  # Debug log
                return redirect(url_for('landing.landing'))
            print(f"Auth successful for {g.user_type}: {g.user.employer_id if g.user_type == 'employer' else g.user.user_id}")  # Debug log
            return f(*args, **kwargs)
        return decorated_function

    if f is None:
        return decorator
    else:
        return decorator(f)