# src/models/user_model.py
import uuid

from ..services.database_service import DynamoDB
import secrets
import datetime

class User:
    def __init__(self, user_id, email, password, first_name, last_name, phone_number, reset_token=None, token_expiration=None):
        self.user_id = user_id or str(uuid.uuid4())  # Generate a UUID if not provided
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
        items = DynamoDB.query_by_email('Users', email)
        if items and len(items) > 0:
            return User(**items[0])
        return None

    @staticmethod
    def get_by_id(user_id):
        item = DynamoDB.get_item('Users', {'user_id': user_id})
        if item:
            return User(**item)
        return None

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
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
                             {'user_id': self.user_id},
                             {'password': new_password, 'reset_token': None, 'token_expiration': None})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number
        }
