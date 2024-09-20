from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
import boto3
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name="ap-southeast-2"
)

registers = Blueprint('registers', __name__)

@registers.route('/UserRegistration', methods=['GET', 'POST'])
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
            print("Passwords do not match!")  # Add a debug print
            return render_template('register_user.html', error=error)

        # Check if user already exists in DynamoDB
        table = dynamodb.Table('Users')
        try:
            response = table.get_item(Key={'email': email})
            print("DynamoDB response:", response)  # Add a debug print
        except Exception as e:
            print("Error accessing DynamoDB:", e)  # Log the error

        if 'Item' in response:
            error = "User already exists!"
            print("User already exists!")  # Add a debug print
            return render_template('register_user.html', error=error)

        # Register the new user (hash password and store in DynamoDB)
        hashed_password = generate_password_hash(password)
        try:
            table.put_item(
                Item={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone_number': phone_number,
                    'password': hashed_password
                }
            )
            print("User registered successfully!")  # Add a debug print
        except Exception as e:
            print("Error inserting into DynamoDB:", e)  # Log the error

        # Redirect to login page after successful registration
        return redirect(url_for('logins.login_user'))

    return render_template('register_user.html')
