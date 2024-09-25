# src/views/login_views.py

from flask import Blueprint, render_template, request, redirect, url_for, make_response, g
import bcrypt
import json
import base64
import logging

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from google.auth.transport.requests import Request

from config import get_secret, store_secret
from ..controllers import UserController, EmployerController, AdminController
from ..services import send_reset_email, SessionManager

from ..services.session_service import SessionManager  # Ensure correct import

logins_bp = Blueprint('logins', __name__)

@logins_bp.route('/Login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = UserController.login(email, password)
        if user:
            # Create a session
            session_id = SessionManager.create_session(user.email)  # Using email as user_id
            if session_id:
                response = make_response(redirect(url_for('index.index')))
                # Set the session cookie (HttpOnly and Secure flags are recommended)
                response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax')
                return response
            else:
                error = "Failed to create session. Please try again."
                return render_template('user/login_user.html', error=error)
        else:
            return render_template('user/login_user.html', error="Invalid email or password.")
    return render_template('user/login_user.html')

@logins_bp.route('/Admin/Login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = AdminController.login(email, password)
        if admin:
            # TODO: Implement admin session management or JWT token issuance
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/login_admin.html', error="Invalid email or password.")
    return render_template('admin/login_admin.html')

@logins_bp.route('/Employer/Login', methods=['GET', 'POST'])
def login_employer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        employer = EmployerController.login(email, password)
        if employer:
            # TODO: Implement employer session management or JWT token issuance
            return redirect(url_for('employer_dashboard'))
        else:
            return render_template('employer/login_employer.html', error="Invalid email or password.")
    return render_template('employer/login_employer.html')

@logins_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        success, message = UserController.reset_password(email)
        return render_template('reset_password.html', success=success, message=message)
    return render_template('reset_password.html')

@logins_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_with_token.html', error="Passwords do not match", token=token)

        success, message = UserController.reset_password_with_token(token, new_password)
        if success:
            return redirect(url_for('logins.login_user', message="Password updated successfully"))
        else:
            return render_template('reset_with_token.html', error=message, token=token)

    return render_template('reset_with_token.html', token=token)

# Logout Route
@logins_bp.route('/logout', methods=['GET'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        SessionManager.delete_session(session_id)
    response = make_response(redirect(url_for('logins.login_user')))
    response.set_cookie('session_id', '', expires=0)
    return response

# Test function for token refresh (optional)
@logins_bp.route('/refresh_token', methods=['GET'])
def refresh_token():
    try:
        credentials = check_and_refresh_token()
        return f"Token refreshed successfully. New expiry: {credentials.expiry}", 200
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return f"Error refreshing token: {str(e)}\n\nTraceback:\n{error_traceback}", 500


def send_email(to, subject, body):
    print("send_email in login_views called")
    try:
        logging.info("Attempting to send email")
        credentials = check_and_refresh_token()
        logging.info(f"Credentials obtained: {credentials}")
        service = build('gmail', 'v1', credentials=credentials)
        logging.info("Gmail service built")

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        logging.info("Email message prepared")

        send_response = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logging.info(f"Email sent successfully. Response: {send_response}")
        return True
    except Exception as e:
        logging.error(f'An error occurred while sending email: {str(e)}')
        logging.exception("Full traceback:")
        return False


def check_and_refresh_token():
    print("check_and_refresh_token in login_views called")
    logging.info("Checking and refreshing token")
    token_json = get_secret('/your-app/token')
    if not token_json:
        raise ValueError("No token found in SSM Parameter Store")

    credentials = Credentials.from_authorized_user_info(json.loads(token_json))
    logging.info(f"Credentials created. Valid: {credentials.valid}, Expired: {credentials.expired}")

    if not credentials.valid or credentials.expired:
        if credentials.refresh_token:
            logging.info("Refreshing token")
            credentials.refresh(Request())
            new_token_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            store_secret('/your-app/token', json.dumps(new_token_data))
            logging.info("Token refreshed and stored")
        else:
            raise ValueError("Refresh token not available. Re-authentication required.")

    return credentials
