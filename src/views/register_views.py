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

@registers.route('/register_user', methods=['GET', 'POST'])
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
            return render_template('register_user.html', error=error)

        # Check if user already exists in DynamoDB
        table = dynamodb.Table('Users')
        response = table.get_item(Key={'email': email})
        if 'Item' in response:
            error = "User already exists!"
            return render_template('register_user.html', error=error)

        # Register the new user (hash password and store in DynamoDB)
        hashed_password = generate_password_hash(password)
        table.put_item(
            Item={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_number': phone_number,
                'password': hashed_password
            }
        )

        # Redirect to login page after successful registration
        return redirect(url_for('logins.login_user'))

    return render_template('register_user.html')
