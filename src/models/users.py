import boto3
from flask import current_app

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

class UserModel:
    def __init__(self):
        self.table = dynamodb.Table('Users')

    def get_user_by_email(self, email):
        response = self.table.get_item(Key={'email': email})
        return response.get('Item')

    def create_user(self, user_data):
        self.table.put_item(Item=user_data)
