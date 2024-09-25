# src/views/index_views.py

from flask import Blueprint, render_template, redirect, url_for, g

from .. import get_user_by_id
from ..decorators.auth_required import auth_required

index_bp = Blueprint('index', __name__)

@index_bp.route('/Index')
@auth_required
def index():
    user = get_user_by_id(g.user.email)  # Pass email instead of the User object
    if user:
        # Pass only specific user details to the template
        user_info = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        return render_template('index.html', user=user_info)
    else:
        return redirect(url_for('logins.login_user'))

@index_bp.route('/')
def redirect_index():
    return redirect("/Index", code=302)
