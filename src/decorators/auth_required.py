from functools import wraps
from flask import g, redirect, url_for


def auth_required(f=None, user_type=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if the user is logged in
            if not g.user:
                print("No user in session, redirecting to landing")
                return redirect(url_for('landing.landing'))

            # If a specific user_type is required, verify it
            if user_type and g.user_type != user_type:
                print(f"User type mismatch. Expected: {user_type}, Got: {g.user_type}")
                return redirect(url_for('landing.landing'))

            # Dynamically access the appropriate identifier based on user_type
            id_attribute = {
                'admin': 'admin_id',
                'employer': 'employer_id',
                'user': 'user_id'
            }.get(g.user_type, None)

            if id_attribute and hasattr(g.user, id_attribute):
                user_id = getattr(g.user, id_attribute)
                print(f"Auth successful for {g.user_type}: {user_id}")
            else:
                print(f"Auth successful for {g.user_type}, but no recognized ID found.")

            return f(*args, **kwargs)

        return decorated_function

    if f is None:
        return decorator
    else:
        return decorator(f)
