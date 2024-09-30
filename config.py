import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2')
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')
    OAUTH_REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8080/user/oauth2callback')

    # Load secrets from AWS SSM Parameter Store
    CLIENT_SECRET = None
    TOKEN = None

    if CLIENT_SECRET is None:
        print(f"Failed to load CLIENT_SECRET from SSM. Raw response: ")

    if TOKEN is None:
        print(f"Failed to load TOKEN from SSM. Raw response: ")

    @classmethod
    def init_app(cls):
        ssm = boto3.client('ssm', region_name=cls.AWS_REGION)
        try:
            client_secret_str = cls.get_secret(ssm, '/your-app/client-secret')
            cls.CLIENT_SECRET = json.loads(client_secret_str)
        except Exception as e:
            print(f"Error loading CLIENT_SECRET: {e}")

        try:
            token_str = cls.get_secret(ssm, '/your-app/token')
            cls.TOKEN = json.loads(token_str) if token_str else None
        except Exception as e:
            print(f"Error loading TOKEN: {e}")

    @staticmethod
    def get_secret(ssm_client, parameter_name):
        try:
            response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
            return response['Parameter']['Value']
        except ClientError as e:
            print(f"Couldn't retrieve parameter {parameter_name}: {e}")
            return None

    @staticmethod
    def store_secret(ssm_client, parameter_name, parameter_value):
        try:
            # If parameter_value is a dict, convert it to a formatted JSON string
            if isinstance(parameter_value, dict):
                parameter_value = json.dumps(parameter_value, indent=2)
            elif not isinstance(parameter_value, str):
                raise ValueError("Parameter value must be a dict or a JSON string")

            # If parameter_value is a string, try to parse it as JSON and reformat it
            else:
                try:
                    json_obj = json.loads(parameter_value)
                    parameter_value = json.dumps(json_obj, indent=2)
                except json.JSONDecodeError:
                    # If it's not valid JSON, keep it as is
                    pass

            ssm_client.put_parameter(
                Name=parameter_name,
                Value=parameter_value,
                Type='SecureString',
                Overwrite=True
            )
            print(f"Successfully stored parameter {parameter_name}")
        except ClientError as e:
            print(f"Couldn't store parameter {parameter_name}: {e}")

# Expose get_secret and store_secret as module-level functions for external access
def get_secret(parameter_name):
    ssm = boto3.client('ssm', region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2'))
    return Config.get_secret(ssm, parameter_name)

def store_secret(parameter_name, parameter_value):
    ssm = boto3.client('ssm', region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2'))
    return Config.store_secret(ssm, parameter_name, parameter_value)
