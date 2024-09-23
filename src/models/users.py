import os
import boto3
import logging

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

class UserModel:
    def __init__(self):
        try:
            self.table = dynamodb.Table('Users')
        except Exception as e:
            logger.error(f"Error initializing DynamoDB Table: {str(e)}")

    def get_user_by_email(self, email):
        """
        Fetch a user from DynamoDB by their email.

        Args:
            email (str): The user's email.

        Returns:
            dict or None: The user's details if found, None otherwise.
        """
        try:
            response = self.table.get_item(Key={'email': email})
            user = response.get('Item')
            if not user:
                logger.info(f"No user found with email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error fetching user by email: {str(e)}")
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
