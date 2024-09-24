from ..services.database_service import DynamoDB
import secrets
import datetime

class Admin:
    def __init__(self, username, email, password, first_name, last_name):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.reset_token = None
        self.token_expiration = None

    def save(self):
        DynamoDB.put_item('Admins', self.__dict__)

    @staticmethod
    def get_by_email(email):
        item = DynamoDB.get_item('Admins', {'email': email})
        if item:
            return Admin(**item)
        return None

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Admins',
                             {'email': self.email},
                             {'reset_token': token, 'token_expiration': expiration.isoformat()})
        self.reset_token = token
        self.token_expiration = expiration
        return token

    @staticmethod
    def get_by_reset_token(token):
        response = DynamoDB.scan('Admins',
                                 FilterExpression='reset_token = :token',
                                 ExpressionAttributeValues={':token': token})
        if response['Items']:
            return Admin(**response['Items'][0])
        return None

    def update_password(self, new_password):
        DynamoDB.update_item('Admins',
                             {'email': self.email},
                             {'password': new_password, 'reset_token': None, 'token_expiration': None})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }