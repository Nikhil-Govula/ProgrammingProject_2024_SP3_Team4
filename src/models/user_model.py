import uuid
from ..services.database_service import DynamoDB
import secrets
import datetime

class User:
    def __init__(self, user_id, email, password, first_name, last_name, phone_number,
                 profile_picture_url=None, certifications=None, reset_token=None, token_expiration=None,
                 failed_login_attempts=0, account_locked=False, city=None, country=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.profile_picture_url = profile_picture_url
        self.certifications = certifications or []
        self.reset_token = reset_token
        self.token_expiration = token_expiration
        self.failed_login_attempts = failed_login_attempts
        self.city = city
        self.country = country

    def save(self):
        DynamoDB.put_item('Users', self.to_dict())

    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked = True
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'failed_login_attempts': self.failed_login_attempts,
                              'account_locked': self.account_locked})

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.account_locked = False
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'failed_login_attempts': 0, 'account_locked': False})

    def lock_account(self):
        self.account_locked = True
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'account_locked': True})

    def unlock_account(self):
        self.account_locked = False
        self.failed_login_attempts = 0
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'account_locked': False, 'failed_login_attempts': 0})

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

    def add_certification(self, cert_id, url, filename):
        cert = {'id': cert_id, 'url': url, 'filename': filename}
        if cert not in self.certifications:
            self.certifications.append(cert)
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'certifications': self.certifications})

    def remove_certification(self, url):
        self.certifications = [cert for cert in self.certifications if cert['url'] != url]
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'certifications': self.certifications})

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'profile_picture_url': self.profile_picture_url,
            'certifications': self.certifications,
            'reset_token': self.reset_token,
            'city': self.city,
            'country': self.country
        }
