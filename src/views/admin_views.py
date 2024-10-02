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
            session_id = SessionManager.create_session(admin.admin_id, 'admin')
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
@auth_required(user_type='admin')
def dashboard():
    admin = AdminController.get_admin_by_id(g.user.admin_id)
    return render_template('admin/dashboard.html', admin=admin)

@admin_bp.route('/logout', methods=['GET'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        SessionManager.delete_session(session_id)
    response = make_response(redirect(url_for('landing.landing')))
    response.set_cookie('session_id', '', expires=0)
    return response

@admin_bp.route('/register', methods=['GET', 'POST'])
@auth_required(user_type='admin')
def register_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Validate form inputs
        if password != confirm_password:
            error = "Passwords do not match!"
            return render_template('admin/register_admin.html', error=error)

        # Register the new admin
        success, message = AdminController.register_admin(email, password, first_name, last_name)
        if success:
            return redirect(url_for('admin_views.dashboard'))
        else:
            return render_template('admin/register_admin.html', error=message)

    return render_template('admin/register_admin.html')

@admin_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        success, message, was_locked = AdminController.reset_password(email)
        return render_template('admin/reset_password.html', success=success, message=message, was_locked=was_locked, email=email)
    return render_template('admin/reset_password.html')

@admin_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('admin/reset_with_token.html', error="Passwords do not match", token=token)

        success, message, was_locked = AdminController.reset_password_with_token(token, new_password)
        if success:
            return redirect(url_for('admin_views.login_admin', message=message))
        else:
            return render_template('admin/reset_with_token.html', error=message, token=token)

    return render_template('admin/reset_with_token.html', token=token)
