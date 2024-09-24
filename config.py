import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = 'secret_key'
    DEBUG = True

def get_secret(parameter_name):
    ssm = boto3.client('ssm', region_name="ap-southeast-2")
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        print(f"Couldn't retrieve parameter {parameter_name}: {e}")
        return None

def store_secret(parameter_name, parameter_value):
    ssm = boto3.client('ssm', region_name="ap-southeast-2")
    try:
        # Ensure the parameter_value is a JSON string
        if isinstance(parameter_value, dict):
            parameter_value = json.dumps(parameter_value)
        elif not isinstance(parameter_value, str):
            raise ValueError("Parameter value must be a dict or a JSON string")

        ssm.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type='SecureString',
            Overwrite=True
        )
        print(f"Successfully stored parameter {parameter_name}")
    except ClientError as e:
        print(f"Couldn't store parameter {parameter_name}: {e}")

# AWS credentials
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION')

# OAuth configuration
client_secret_str = get_secret('/your-app/client-secret')
token_str = get_secret('/your-app/token')

try:
    CLIENT_SECRET = json.loads(client_secret_str)
except json.JSONDecodeError as e:
    print(f"Error decoding client secret JSON: {e}")
    print(f"Raw client secret: {client_secret_str}")
    CLIENT_SECRET = None

try:
    TOKEN = json.loads(token_str) if token_str else None
except json.JSONDecodeError as e:
    print(f"Error decoding token JSON: {e}")
    print(f"Raw token: {token_str}")
    TOKEN = None