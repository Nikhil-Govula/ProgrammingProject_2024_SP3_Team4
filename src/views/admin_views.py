# src/views/admin_views.py

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g
from functools import wraps
import bcrypt

from ..controllers import AdminController
from ..decorators.auth_required import auth_required
from ..services import SessionManager

admin_bp = Blueprint('admin_views', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin, error_message = AdminController.login(email, password)
        if admin:
            session_id = SessionManager.create_session(admin.email, 'admin')
            if session_id:
                response = make_response(redirect(url_for('admin_views.dashboard')))
                response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax')
                return response
            else:
                error = "Failed to create session. Please try again."
                return render_template('admin/login_admin.html', error=error)
        else:
            return render_template('admin/login_admin.html', error=error_message)
    return render_template('admin/login_admin.html')

@admin_bp.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    admin = g.user
    return render_template('admin/dashboard.html', admin=admin)

@admin_bp.route('/logout', methods=['GET'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        SessionManager.delete_session(session_id)
    response = make_response(redirect(url_for('landing.landing')))
    response.set_cookie('session_id', '', expires=0)
    return response
