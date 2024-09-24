import base64
import json
from email.mime.text import MIMEText

from flask import Blueprint, render_template, request, redirect, url_for
import boto3
import bcrypt
import logging

from flask_mail import Mail
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import CLIENT_SECRET, store_secret, get_secret
from src.controllers.user_controller import UserController

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logins = Blueprint('logins', __name__)

# Specify the region when initializing the boto3 clients
ssm = boto3.client('ssm', region_name='ap-southeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

# Connect to DynamoDB table
users_table = dynamodb.Table('Users')

# Retrieve password from Parameter Store
def get_db_password():
    try:
        parameter = ssm.get_parameter(Name='/project/db_password', WithDecryption=True)
        logging.debug(f"Successfully retrieved parameter: {parameter['Parameter']['Name']}")
        return parameter['Parameter']['Value']
    except Exception as e:
        logging.error(f"Failed to access Parameter Store: {str(e)}")
        return None

# Login view for users
@logins.route('/Login', methods=['GET', 'POST'])
def index_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        logging.debug(f"Attempting login for user: {email}")

        # Retrieve user from DynamoDB
        try:
            response = users_table.get_item(
                Key={
                    'username': email
                }
            )
            user = response.get('Item')

            if user:
                logging.debug(f"User found: {user['username']}")
            else:
                logging.warning(f"No user found with email: {email}")
                return render_template('user/login_user.html', error="Invalid email or password.")

            # Check if user exists and password matches
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                logging.debug(f"Password match for user: {email}")
                # Redirect to the dashboard or home page
                return redirect(url_for('index.index'))
            else:
                logging.warning(f"Password mismatch for user: {email}")
                return render_template('user/login_user.html', error="Invalid email or password.")

        except Exception as e:
            logging.error(f"Error during login process for user {email}: {str(e)}")
            return render_template('user/login_user.html', error="An error occurred. Please try again.")

    return render_template('user/login_user.html')


@logins.route('/Admin/Login', methods=['GET', 'POST'])
def index_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        logging.debug(f"Attempting admin login for user: {email}")

        # Retrieve admin user from DynamoDB
        try:
            response = users_table.get_item(
                Key={
                    'username': email
                }
            )
            admin = response.get('Item')

            if admin:
                logging.debug(f"Admin user found: {admin['username']}")
            else:
                logging.warning(f"No admin user found with email: {email}")
                return render_template('admin/login_admin.html', error="Invalid email or password.")

            # Check if admin exists and password matches
            if bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
                logging.debug(f"Password match for admin user: {email}")
                # Redirect to the admin dashboard
                return redirect(url_for('admin_dashboard'))
            else:
                logging.warning(f"Password mismatch for admin user: {email}")
                return render_template('admin/login_admin.html', error="Invalid email or password.")

        except Exception as e:
            logging.error(f"Error during admin login process for user {email}: {str(e)}")
            return render_template('admin/login_admin.html', error="An error occurred. Please try again.")

    return render_template('admin/login_admin.html')


@logins.route('/Employer/Login', methods=['GET', 'POST'])
def index_employer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        logging.debug(f"Attempting employer login for user: {email}")

        # Retrieve employer user from DynamoDB
        try:
            response = users_table.get_item(
                Key={
                    'username': email
                }
            )
            employer = response.get('Item')

            if employer:
                logging.debug(f"Company user found: {employer['username']}")
            else:
                logging.warning(f"No employer user found with email: {email}")
                return render_template('employer/login_employer.html', error="Invalid email or password.")

            # Check if employer user exists and password matches
            if bcrypt.checkpw(password.encode('utf-8'), employer['password'].encode('utf-8')):
                logging.debug(f"Password match for employer user: {email}")
                # Redirect to the employer dashboard
                return redirect(url_for('company_dashboard'))
            else:
                logging.warning(f"Password mismatch for employer user: {email}")
                return render_template('employer/login_employer.html', error="Invalid email or password.")

        except Exception as e:
            logging.error(f"Error during employer login process for user {email}: {str(e)}")
            return render_template('employer/login_employer.html', error="An error occurred. Please try again.")

    return render_template('employer/login_employer.html')

@logins.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        success, message = UserController.reset_password(email)
        return render_template('reset_password.html', success=success, message=message)
    return render_template('reset_password.html')


@logins.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_with_token.html', error="Passwords do not match", token=token)

        success, message = UserController.reset_password_with_token(token, new_password)
        if success:
            return redirect(url_for('logins.index_user', message="Password updated successfully"))
        else:
            return render_template('reset_with_token.html', error=message, token=token)

    return render_template('reset_with_token.html', token=token)

# Test function for token refresh
@logins.route('/refresh_token', methods=['GET'])
def refresh_token():
    try:
        credentials = check_and_refresh_token()
        return f"Token refreshed successfully. New expiry: {credentials.expiry}", 200
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return f"Error refreshing token: {str(e)}\n\nTraceback:\n{error_traceback}", 500


mail = Mail()

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
    print("send_reset_email in login_views called")
    try:
        token_json = get_secret('/your-app/token')
        if not token_json:
            raise ValueError("No token found in SSM Parameter Store")

        credentials = Credentials.from_authorized_user_info(json.loads(token_json))
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


# Initialize OAuth 2.0 flow using the client secret
flow = Flow.from_client_config(
    CLIENT_SECRET,
    scopes=['https://www.googleapis.com/auth/gmail.send']
)
flow.redirect_uri = 'http://localhost:8080/oauth2callback'


@logins.route('/authorize')
def authorize():
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return redirect(authorization_url)

@logins.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Format the token data as a dictionary
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None
    }

    # Store the formatted token data in SSM
    store_secret('/your-app/token', json.dumps(token_data))
    return 'Authentication successful'
