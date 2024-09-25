from flask import Blueprint, render_template, request, redirect, url_for, current_app
import bcrypt
import json
import base64
import logging

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText

from ..controllers import UserController, EmployerController, AdminController
from ..services import send_reset_email




logins_bp = Blueprint('logins', __name__)


@logins_bp.route('/Login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = UserController.login(email, password)
        if user:
            # TODO: Implement session management or JWT token issuance
            return redirect(url_for('index.index'))
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

# Test function for token refresh
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

def send_reset_email(email, token):
    try:
        flow = current_app.flow
        credentials = Credentials.from_authorized_user_info(current_app.config['TOKEN'])
        service = build('gmail', 'v1', credentials=credentials)

        reset_link = url_for('logins.reset_with_token', token=token, _external=True)
        subject = 'Password Reset Request'
        body = f'''To reset your password, visit the following link:
{reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''

        message = MIMEText(body)
        message['to'] = email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logging.info("Email sent successfully via Gmail API")
        return True
    except Exception as e:
        logging.error(f"Error sending email via Gmail API: {str(e)}")
        return False


def check_and_refresh_token():
    print("check_and_refresh_token in login_views called")
    logging.info("Checking and refreshing token")
    token_json = get_secret('/your-app/token')
    if not token_json:
        raise ValueError("No token found in SSM Parameter Store")

    # token_data = json.loads(token_json)
    # logging.info(f"Token data retrieved: {token_data}")

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



