from functools import wraps
from flask import g, redirect, url_for

def auth_required(f=None, user_type=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                return redirect(url_for('landing.landing'))
            if user_type and getattr(g, 'user_type', None) != user_type:
                return redirect(url_for('landing.landing'))
            return f(*args, **kwargs)
        return decorated_function

    if f is None:
        return decorator
    else:
        return decorator(f)
