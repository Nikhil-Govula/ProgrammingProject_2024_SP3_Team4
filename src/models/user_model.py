import datetime
import os
import secrets

import boto3
import logging
from ..services.database_service import DynamoDB

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User:
    def __init__(self, username, email, password, first_name, last_name, phone_number, reset_token=None, token_expiration=None):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.reset_token = reset_token
        self.token_expiration = token_expiration

    def save(self):
        DynamoDB.put_item('Users', self.__dict__)

    @staticmethod
    def get_by_email(email):
        response = DynamoDB.scan('Users',
                                 FilterExpression='email = :email',
                                 ExpressionAttributeValues={':email': email})
        if response and 'Items' in response and response['Items']:
            return User(**response['Items'][0])
        return None

    def create_user(self, user_data):
        """
        Create a new user in DynamoDB.

        Args:
            user_data (dict): The user's details.

        Returns:
            bool: True if the user was created successfully, False otherwise.
        """
        try:
            # Check if the user already exists
            if self.get_user_by_email(user_data['email']):
                logger.info(f"User already exists with email: {user_data['email']}")
                return False

            self.table.put_item(Item=user_data)
            logger.info(f"User created successfully with email: {user_data['email']}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def update_user_password(self, email, new_password):
        """
        Update the user's password in DynamoDB.

        Args:
            email (str): The user's email.
            new_password (str): The new password to be set.

        Returns:
            bool: True if the password was updated successfully, False otherwise.
        """
        try:
            response = self.table.update_item(
                Key={'email': email},
                UpdateExpression="set #pwd = :p",
                ExpressionAttributeNames={'#pwd': 'password'},
                ExpressionAttributeValues={':p': new_password}
            )
            logger.info(f"Password updated successfully for user: {email}")
            return True
        except Exception as e:
            logger.error(f"Error updating password for user: {str(e)}")
            return False

    def delete_user(self, email):
        """
        Delete a user from DynamoDB by their email.

        Args:
            email (str): The user's email.

        Returns:
            bool: True if the user was deleted successfully, False otherwise.
        """
        try:
            self.table.delete_item(Key={'email': email})
            logger.info(f"User deleted successfully with email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Users',
                             {'username': self.email},
                             {'reset_token': token, 'token_expiration': expiration.isoformat()})
        self.reset_token = token
        self.token_expiration = expiration
        return token

    @staticmethod
    def get_by_reset_token(token):
        response = DynamoDB.scan('Users',
                                 FilterExpression='reset_token = :token',
                                 ExpressionAttributeValues={':token': token})
        if response['Items']:
            return User(**response['Items'][0])
        return None

    def update_password(self, new_password):
        DynamoDB.update_item('Users',
                             {'username': self.email},
                             {'password': new_password, 'reset_token': None, 'token_expiration': None})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number
        }