from ..services.database_service import DynamoDB
import secrets
import datetime
import uuid

class Employer:
    def __init__(self, employer_id, company_name, email, password, contact_person, phone_number,
                 failed_login_attempts=0, account_locked=False,
                 reset_token=None, token_expiration=None, is_active=True):
        self.employer_id = employer_id or str(uuid.uuid4())
        self.company_name = company_name
        self.email = email
        self.password = password
        self.contact_person = contact_person
        self.phone_number = phone_number
        self.failed_login_attempts = failed_login_attempts
        self.account_locked = account_locked
        self.reset_token = reset_token
        self.token_expiration = token_expiration
        self.is_active = is_active

    def save(self):
        return DynamoDB.put_item('Employers', self.to_dict())

    @staticmethod
    def get_by_email(email):
        items = DynamoDB.query_by_email('Employers', email)
        if items and len(items) > 0:
            return Employer(**items[0])
        return None

    @staticmethod
    def get_by_id(employer_id):
        item = DynamoDB.get_item('Employers', {'employer_id': employer_id})
        if item:
            return Employer(**item)
        return None

    @staticmethod
    def get_all_employers():
        items = DynamoDB.scan('Employers')
        return [Employer(**item) for item in items.get('Items', [])]

    def increment_failed_attempts(self, threshold=5):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= threshold:
            self.account_locked = True
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'failed_login_attempts': self.failed_login_attempts,
                              'account_locked': self.account_locked})

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'failed_login_attempts': 0})

    def lock_account(self):
        self.account_locked = True
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'account_locked': True})

    def unlock_account(self):
        self.account_locked = False
        self.failed_login_attempts = 0
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'account_locked': False,
                              'failed_login_attempts': 0})

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'reset_token': token,
                              'token_expiration': expiration.isoformat()})
        self.reset_token = token
        self.token_expiration = expiration
        return token

    @staticmethod
    def get_by_reset_token(token):
        response = DynamoDB.scan('Employers',
                                 FilterExpression='reset_token = :token',
                                 ExpressionAttributeValues={':token': token})
        if response['Items']:
            return Employer(**response['Items'][0])
        return None

    def update_password(self, new_password):
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'password': new_password,
                              'reset_token': None,
                              'token_expiration': None,
                              'failed_login_attempts': 0,
                              'account_locked': False})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None
        self.failed_login_attempts = 0
        self.account_locked = False

    def toggle_active_status(self):
        self.is_active = not self.is_active
        DynamoDB.update_item('Employers',
                             {'employer_id': self.employer_id},
                             {'is_active': self.is_active})
        print(f"Employer {self.employer_id} active status toggled to: {self.is_active}")  # Debug log

    def to_dict(self):
        return {
            'employer_id': self.employer_id,
            'company_name': self.company_name,
            'email': self.email,
            'password': self.password,
            'contact_person': self.contact_person,
            'phone_number': self.phone_number,
            'is_active': self.is_active,
            'account_locked': self.account_locked
        }

    def update_fields(self, fields):
        try:
            for key, value in fields.items():
                if hasattr(self, key) and key not in ['employer_id']:
                    setattr(self, key, value)
            self.save()
            return True, "Employer updated successfully."
        except Exception as e:
            print(f"Error updating Employer: {e}")
            return False, str(e)