from ..services.database_service import DynamoDB
import secrets
import datetime
import uuid

class Admin:
    def __init__(self, admin_id, email, password, first_name, last_name, failed_login_attempts=0, account_locked=False,
                 reset_token=None, token_expiration=None, is_active=True):
        self.admin_id = admin_id or str(uuid.uuid4())
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.failed_login_attempts = failed_login_attempts
        self.account_locked = account_locked
        self.reset_token = reset_token
        self.token_expiration = token_expiration
        self.is_active = is_active

    def save(self):
        return DynamoDB.put_item('Admins', self.to_dict())

    @staticmethod
    def get_by_id(admin_id):
        item = DynamoDB.get_item('Admins', {'admin_id': admin_id})
        if item:
            return Admin(**item)
        return None

    @staticmethod
    def get_by_email(email):
        response = DynamoDB.scan('Admins',
                                 FilterExpression='email = :email',
                                 ExpressionAttributeValues={':email': email})
        items = response.get('Items', [])
        if items:
            return Admin(**items[0])
        return None

    def increment_failed_attempts(self, threshold=5):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= threshold:
            self.account_locked = True
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'failed_login_attempts': self.failed_login_attempts,
                              'account_locked': self.account_locked})

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'failed_login_attempts': 0})

    def lock_account(self):
        self.account_locked = True
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'account_locked': True})

    def unlock_account(self):
        self.account_locked = False
        self.failed_login_attempts = 0
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'account_locked': False,
                              'failed_login_attempts': 0})

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'reset_token': token, 'token_expiration': expiration.isoformat()})
        self.reset_token = token
        self.token_expiration = expiration
        return token

    @staticmethod
    def get_by_reset_token(token):
        response = DynamoDB.scan('Admins',
                                 FilterExpression='reset_token = :token',
                                 ExpressionAttributeValues={':token': token})
        items = response.get('Items', [])
        if items:
            return Admin(**items[0])
        return None

    def update_password(self, new_password):
        DynamoDB.update_item('Admins',
                             {'admin_id': self.admin_id},
                             {'password': new_password, 'reset_token': None, 'token_expiration': None})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None
        self.failed_login_attempts = 0
        self.account_locked = False

    def to_dict(self):
        return {
            'admin_id': self.admin_id,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'reset_token': self.reset_token,
            'token_expiration': self.token_expiration,
            'is_active': self.is_active
        }

    @staticmethod
    def get_all_active_admins():
        items = DynamoDB.get_all_active_admins()
        return [Admin(**item) for item in items]

    @staticmethod
    def get_all_admins():
        items = DynamoDB.get_all_admins()
        return [Admin(**item) for item in items]

    def update_fields(self, fields):
        try:
            # Update only the provided fields
            for key, value in fields.items():
                if hasattr(self, key) and key not in ['admin_id']:
                    setattr(self, key, value)
            self.save()
            return True, "Admin updated successfully."
        except Exception as e:
            print(f"Error updating Admin: {e}")
            return False, str(e)


def update_single_field(self, field, value):
    """Update a single field for the admin."""
    if hasattr(self, field):
        setattr(self, field, value)
        try:
            update_values = {field: value}
            success = DynamoDB.update_item(
                'Admins',
                {'admin_id': self.admin_id},
                update_values
            )
            return success
        except Exception as e:
            print(f"Error updating field {field}: {e}")
            return False
    return False