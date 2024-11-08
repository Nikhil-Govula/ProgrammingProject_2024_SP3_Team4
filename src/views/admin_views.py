# Filename: src/views/admin_views.py

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, jsonify, flash
from functools import wraps
import bcrypt
import logging

from ..controllers import AdminController
from ..decorators.auth_required import auth_required
from ..models import AuditLog
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
        return render_template('admin/reset_password.html', success=success, message=message, was_locked=was_locked,
                               email=email)
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


@admin_bp.route('/manage_accounts', methods=['GET'])
@auth_required(user_type='admin')
def manage_accounts():
    account_type = request.args.get('account_type', default='user', type=str).lower()
    account_status = request.args.get('account_status', default='', type=str)
    search_query = request.args.get('search', default='', type=str)

    # Split account_status into a list
    status_filters = account_status.split(',')

    # Fetch accounts
    accounts = AdminController.get_all_accounts(account_type=account_type,
                                                account_status=status_filters,
                                                search_query=search_query)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('admin/manage_accounts.html',
                               accounts=accounts,
                               account_type=account_type,
                               account_status=account_status,
                               search_query=search_query)

    return render_template('admin/manage_accounts.html',
                           accounts=accounts,
                           account_type=account_type,
                           account_status=account_status,
                           search_query=search_query)


@admin_bp.route('/create_account', methods=['GET', 'POST'])
@auth_required(user_type='admin')
def create_account():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        account_type = request.form.get('account_type', 'user')  # Default to 'user' if not specified

        if account_type == 'user':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone_number = request.form['phone_number']
            location = request.form['location']
            skills = request.form['skills'].split(',') if request.form['skills'] else []
            success, message = AdminController.create_user_account(email, password, first_name, last_name, phone_number,
                                                                   location, skills)
        elif account_type == 'employer':
            company_name = request.form['company_name']
            contact_person = request.form['contact_person']
            phone_number = request.form['employer_phone']
            success, message = AdminController.create_employer_account(email, password, company_name, contact_person,
                                                                       phone_number)
        elif account_type == 'admin':
            first_name = request.form['admin_first_name']
            last_name = request.form['admin_last_name']
            success, message = AdminController.create_admin_account(email, password, first_name, last_name)
        else:
            return render_template('admin/create_account.html', error="Invalid account type")

        if success:
            flash(f"{account_type.capitalize()} account created successfully", "success")
            return redirect(url_for('admin_views.manage_accounts'))
        else:
            flash(message, "error")
            return render_template('admin/create_account.html', error=message)
    return render_template('admin/create_account.html')


@admin_bp.route('/account/<account_type>/<account_id>', methods=['GET', 'POST'])
@auth_required(user_type='admin')
def account_detail(account_type, account_id):
    account = AdminController.get_account_by_id(account_id, account_type)
    if not account:
        return "Account not found.", 404

    if request.method == 'POST':
        action = request.form.get('action')
        if action in ['toggle_account_lock', 'toggle_account_activation']:
            if action == 'toggle_account_lock':
                success, message = AdminController.toggle_account_lock(account_id, account_type)
            elif action == 'toggle_account_activation':
                success, message = AdminController.toggle_account_activation(account_id, account_type)
            return jsonify({'success': success, 'message': message})
        else:
            # Handle account update
            update_data = {}
            if account_type.lower() in ['admin', 'user']:
                update_data['first_name'] = request.form.get('first_name')
                update_data['last_name'] = request.form.get('last_name')

            update_data['email'] = request.form.get('email')
            update_data['phone_number'] = request.form.get('phone_number')

            if account_type.lower() == 'user':
                update_data['location'] = request.form.get('location')
            elif account_type.lower() == 'employer':
                update_data['company_name'] = request.form.get('company_name')
                update_data['contact_person'] = request.form.get('contact_person')

            password = request.form.get('password')
            if password:
                update_data['password'] = password

            success, message = AdminController.update_account(account_id, account_type, **update_data)

            if success:
                return redirect(url_for('admin_views.account_detail', account_type=account_type, account_id=account_id))
            else:
                return render_template('admin/account_detail.html', account=account, account_type=account_type,
                                       error=message)

    return render_template('admin/account_detail.html', account=account, account_type=account_type)


@admin_bp.route('/account/<account_type>/<account_id>/deactivate', methods=['POST'])
@auth_required(user_type='admin')
def deactivate_account(account_type, account_id):
    success, message = AdminController.deactivate_account(account_id, account_type)
    if success:
        return redirect(url_for('admin_views.manage_accounts'))
    else:
        return jsonify({'success': False, 'message': message}), 400


@admin_bp.route('/audit_logs', methods=['GET'])
@auth_required(user_type='admin')
def view_audit_logs():
    logs = AuditLog.get_all_logs()
    return render_template('admin/audit_logs.html', logs=logs)


@admin_bp.route('/account/<account_type>/<account_id>/toggle_lock', methods=['POST'])
@auth_required(user_type='admin')
def toggle_account_lock(account_type, account_id):
    success, message = AdminController.toggle_account_lock(account_id, account_type)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400


@admin_bp.route('/account/<account_type>/<account_id>/toggle_activation', methods=['POST'])
@auth_required(user_type='admin')
def toggle_account_activation(account_type, account_id):
    success, message = AdminController.toggle_account_activation(account_id, account_type)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400


@admin_bp.route('/account/<account_type>/<account_id>/update_field', methods=['POST'])
@auth_required(user_type='admin')
def update_field(account_type, account_id):
    """
    Endpoint to update a single field of an account.
    Expects JSON data with 'field' and 'value'.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'}), 400

    field = data.get('field')
    value = data.get('value')

    if not field:
        return jsonify({'success': False, 'message': 'No field specified.'}), 400

    # Define allowed fields for each account type
    allowed_fields = {
        'admin': ['first_name', 'last_name', 'email', 'phone_number', 'password'],
        'user': ['first_name', 'last_name', 'email', 'phone_number', 'location', 'password'],
        'employer': ['company_name', 'contact_person', 'email', 'phone_number', 'password']
    }

    if field not in allowed_fields.get(account_type.lower(), []):
        return jsonify({'success': False, 'message': 'Invalid field.'}), 400

    # Additional validation based on field
    if field == 'email':
        import re
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, value):
            return jsonify({'success': False, 'message': 'Invalid email format.'}), 400

    if field == 'password':
        # Implement password strength validation
        is_valid, message = AdminController.validate_password(value)
        if not is_valid:
            return jsonify({'success': False, 'message': message}), 400

    # Prepare update data
    update_data = {}
    if field == 'location' and account_type.lower() == 'user':
        # Split location into city and country
        try:
            city, country = map(str.strip, value.split(',', 1))
            update_data['location'] = value
            update_data['city'] = city
            update_data['country'] = country
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid location format. Use "City, Country".'}), 400
    elif field == 'password':
        update_data['password'] = value  # Password will be hashed in AdminController
    else:
        update_data[field] = value

    # Update the account
    success, message = AdminController.update_account(account_id, account_type, **update_data)

    if success:
        # If the updated field is password, do not send the hashed password back
        updated_value = None
        if field != 'password':
            updated_value = value

        return jsonify({'success': True, 'message': message, 'updated_value': updated_value}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400
