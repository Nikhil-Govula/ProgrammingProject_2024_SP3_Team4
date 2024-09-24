import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

class Employer:
    def __init__(self):
        self.table = dynamodb.Table('Employers')

    def create_employer(self, employer_data):
        self.table.put_item(Item=employer_data)

    def get_employer(self, employer_id):
        response = self.table.get_item(Key={'employer_id': employer_id})
        return response.get('Item')

    def update_employer(self, employer_id, update_data):
        # Update employer data here
        pass
