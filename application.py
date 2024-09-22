import json

from botocore.exceptions import ClientError
from flask_mail import Mail
from flask import Flask, redirect, request
from src import create_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os
import boto3
from dotenv import load_dotenv
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Load environment variables from .env file
load_dotenv()
print(os.environ)

mail = Mail()

def get_secret(parameter_name):
    ssm = boto3.client('ssm', region_name="ap-southeast-2")
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        print(f"Couldn't retrieve parameter {parameter_name}: {e}")
        return None

# Use the function to get your secrets
client_secret_str = get_secret('/your-app/client-secret')
token_str = get_secret('/your-app/token')

try:
    client_secret = json.loads(client_secret_str)
except json.JSONDecodeError as e:
    print(f"Error decoding client secret JSON: {e}")
    print(f"Raw client secret: {client_secret_str}")
    client_secret = None

try:
    token = json.loads(token_str)
except json.JSONDecodeError as e:
    print(f"Error decoding token JSON: {e}")
    print(f"Raw token: {token_str}")
    token = None

if client_secret is None or token is None:
    print("Failed to load necessary secrets. Exiting.")
    exit(1)

# Initialize OAuth 2.0 flow using the client secret
flow = Flow.from_client_config(
    client_secret,
    scopes=['https://www.googleapis.com/auth/gmail.send']
)
flow.redirect_uri = 'http://localhost:8080/oauth2callback'

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


def create_application():
    app = create_app()

    # OAuth routes
    @app.route('/authorize')
    def authorize():
        authorization_url, _ = flow.authorization_url(prompt='consent')
        return redirect(authorization_url)

    @app.route('/oauth2callback')
    def oauth2callback():
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        # Store these credentials for future use
        with open('token.json', 'w') as token_file:
            token_file.write(credentials.to_json())
        return 'Authentication successful'

    return app


application = app = create_application()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True)