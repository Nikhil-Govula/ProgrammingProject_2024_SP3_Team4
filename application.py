from src import create_app

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

application = app = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True)