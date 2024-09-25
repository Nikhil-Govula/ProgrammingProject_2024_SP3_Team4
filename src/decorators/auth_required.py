# src/decorators/auth_required.py

from functools import wraps
from flask import g, redirect, url_for, request

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            # Optionally, store the original destination
            return redirect(url_for('logins.login_user', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
