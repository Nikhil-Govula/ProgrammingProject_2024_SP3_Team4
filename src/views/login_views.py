from flask import Blueprint, render_template, request, redirect, url_for
import boto3
import bcrypt
import logging

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
        # Logic to send the reset link to the user's email
        # ...
        return render_template('reset_password.html', success="A reset link has been sent to your email.")
    return render_template('reset_password.html')
