from ..services.database_service import DynamoDB
import secrets
import datetime

class Employer:
    def __init__(self, company_name, email, password, contact_person, phone_number):
        self.company_name = company_name
        self.email = email
        self.password = password
        self.contact_person = contact_person
        self.phone_number = phone_number
        self.reset_token = None
        self.token_expiration = None

    def save(self):
        DynamoDB.put_item('Employers', self.__dict__)

    @staticmethod
    def get_by_email(email):
        item = DynamoDB.get_item('Employers', {'email': email})
        if item:
            return Employer(**item)
        return None

    def generate_reset_token(self):
        token = secrets.token_urlsafe()
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        DynamoDB.update_item('Employers',
                             {'email': self.email},
                             {'reset_token': token, 'token_expiration': expiration.isoformat()})
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
                             {'email': self.email},
                             {'password': new_password, 'reset_token': None, 'token_expiration': None})
        self.password = new_password
        self.reset_token = None
        self.token_expiration = None

    def to_dict(self):
        return {
            'company_name': self.company_name,
            'email': self.email,
            'contact_person': self.contact_person,
            'phone_number': self.phone_number
        }