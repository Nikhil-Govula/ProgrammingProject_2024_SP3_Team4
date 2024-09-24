from flask_mail import Mail
from flask import redirect, request, url_for
from src import create_app, logins
from google_auth_oauthlib.flow import Flow
from config import CLIENT_SECRET, store_secret
import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve AWS credentials and region from environment variables
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_DEFAULT_REGION')

# Initialize boto3 clients using the loaded credentials
ssm = boto3.client(
    'ssm',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name="ap-southeast-2"
)

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name="ap-southeast-2"
)

mail = Mail()

# Initialize OAuth 2.0 flow using the client secret
flow = Flow.from_client_config(
    CLIENT_SECRET,
    scopes=['https://www.googleapis.com/auth/gmail.send']
)
flow.redirect_uri = 'http://localhost:8080/oauth2callback'

def create_application():
    app = create_app()
    mail.init_app(app)
    return app

application = app = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True)