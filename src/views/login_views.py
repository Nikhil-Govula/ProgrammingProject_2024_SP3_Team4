import base64
import datetime
import secrets
from email.mime.text import MIMEText

from botocore.exceptions import ClientError
from flask import Blueprint, render_template, request, redirect, url_for
import boto3
import bcrypt
import logging

from flask_mail import Mail, Message
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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


@logins.route('/Company/Login', methods=['GET', 'POST'])
def index_company():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        logging.debug(f"Attempting company login for user: {email}")

        # Retrieve company user from DynamoDB
        try:
            response = users_table.get_item(
                Key={
                    'username': email
                }
            )
            company = response.get('Item')

            if company:
                logging.debug(f"Company user found: {company['username']}")
            else:
                logging.warning(f"No company user found with email: {email}")
                return render_template('company/login_company.html', error="Invalid email or password.")

            # Check if company user exists and password matches
            if bcrypt.checkpw(password.encode('utf-8'), company['password'].encode('utf-8')):
                logging.debug(f"Password match for company user: {email}")
                # Redirect to the company dashboard
                return redirect(url_for('company_dashboard'))
            else:
                logging.warning(f"Password mismatch for company user: {email}")
                return render_template('company/login_company.html', error="Invalid email or password.")

        except Exception as e:
            logging.error(f"Error during company login process for user {email}: {str(e)}")
            return render_template('company/login_company.html', error="An error occurred. Please try again.")

    return render_template('company/login_company.html')

mail = Mail()


def send_email(to, subject, body):
    try:
        credentials = Credentials.from_authorized_user_file('token.json')
        service = build('gmail', 'v1', credentials=credentials)

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return True
    except Exception as e:
        logging.error(f'An error occurred while sending email: {e}')
        return False

@logins.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        # Generate token
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        try:
            # Store token in DynamoDB
            users_table.update_item(
                Key={'username': email},
                UpdateExpression="SET reset_token = :token, token_expiration = :exp",
                ExpressionAttributeValues={
                    ':token': token,
                    ':exp': expiration.isoformat()
                }
            )

            # Send reset email using OAuth 2.0
            reset_link = url_for('logins.reset_with_token', token=token, _external=True)
            subject = 'Password Reset Request'
            body = f'''To reset your password, visit the following link:
{reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
            if send_email(email, subject, body):
                return render_template('reset_password.html', success="Reset link sent to your email.")
            else:
                return render_template('reset_password.html', error="Failed to send reset email. Please try again.")

        except Exception as e:
            logging.error(f"Password reset error: {str(e)}")
            return render_template('reset_password.html', error="An error occurred. Please try again.")

    return render_template('reset_password.html')


@logins.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_with_token.html', error="Passwords do not match", token=token)

        try:
            # Find user with this token
            response = users_table.scan(
                FilterExpression='reset_token = :token',
                ExpressionAttributeValues={':token': token}
            )

            if response['Items']:
                user = response['Items'][0]
                if datetime.datetime.utcnow() < datetime.datetime.fromisoformat(user['token_expiration']):
                    # Update password
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    users_table.update_item(
                        Key={'username': user['username']},
                        UpdateExpression="SET password = :pwd REMOVE reset_token, token_expiration",
                        ExpressionAttributeValues={':pwd': hashed_password.decode('utf-8')}
                    )
                    return redirect(url_for('logins.index_user', message="Password updated successfully"))
                else:
                    return render_template('reset_with_token.html', error="Token expired", token=token)
            else:
                return render_template('reset_with_token.html', error="Invalid token", token=token)
        except Exception as e:
            logging.error(f"Password reset error: {str(e)}")
            return render_template('reset_with_token.html', error="An error occurred", token=token)

    return render_template('reset_with_token.html', token=token)


def send_reset_email(email, token):
    msg = Message('Password Reset Request',
                  recipients=[email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('logins.reset_with_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False


