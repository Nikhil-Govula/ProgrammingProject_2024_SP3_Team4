import logging
import uuid

from flask import Blueprint, render_template, request, redirect, url_for
import bcrypt
import boto3
import os

from src.controllers import UserController
from src.services import DynamoDB

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name="ap-southeast-2"
)

registers_bp = Blueprint('registers', __name__)

@registers_bp.route('/UserRegistration', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate form inputs
        if password != confirm_password:
            error = "Passwords do not match!"
            logging.debug("Passwords do not match!")
            return render_template('user/register_user.html', error=error)

        # Validate password
        is_valid, message = UserController.validate_password(password)
        if not is_valid:
            logging.debug(f"Password validation failed: {message}")
            return render_template('user/register_user.html', error=message)

        # Register the new user
        success, message = UserController.register_user(email, password, first_name, last_name, phone_number)
        if success:
            logging.info("User registered successfully!")
            return redirect(url_for('logins.login_user'))
        else:
            logging.error(f"User registration failed: {message}")
            return render_template('user/register_user.html', error=message)

    return render_template('user/register_user.html')

@registers_bp.route('/EmployerRegistration', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        company_name = request.form['company_name']
        contact_person = request.form['contact_person']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate form inputs
        if password != confirm_password:
            error = "Passwords do not match!"
            logging.debug("Passwords do not match!")
            return render_template('employer/register_employer.html', error=error)

        # Check if employer already exists in DynamoDB
        table = dynamodb.Table('Companies')
        try:
            response = table.get_item(Key={'email': email})
            logging.debug(f"DynamoDB response: {response}")
        except Exception as e:
            logging.error(f"Error accessing DynamoDB: {e}")
            error = "Internal server error. Please try again later."
            return render_template('employer/register_employer.html', error=error)

        if 'Item' in response:
            error = "Company already exists!"
            logging.debug("Company already exists!")
            return render_template('employer/register_employer.html', error=error)

        # Register the new employer (hash password and store in DynamoDB)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            table.put_item(
                Item={
                    'company_name': company_name,
                    'contact_person': contact_person,
                    'email': email,
                    'phone_number': phone_number,
                    'password': hashed_password.decode('utf-8')
                }
            )
            logging.info("Employer registered successfully!")
        except Exception as e:
            logging.error(f"Error inserting into DynamoDB: {e}")
            error = "Internal server error. Please try again later."
            return render_template('employer/register_employer.html', error=error)

        # Redirect to login page after successful registration
        return redirect(url_for('logins.login_employer'))

    return render_template('employer/register_employer.html')