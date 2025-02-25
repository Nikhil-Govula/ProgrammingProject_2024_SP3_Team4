import uuid

from flask import request

from ..services.database_service import DynamoDB
import secrets
import datetime

class User:
    def __init__(self, user_id, email, password, first_name, last_name, phone_number,
                 profile_picture_url=None, certifications=None, reset_token=None, token_expiration=None,
                 verification_token=None, verification_token_expiration=None,
                 failed_login_attempts=0, account_locked=False, city=None, country=None,
                 work_history=None, skills=None, saved_jobs=None, applications=None, is_active=False):
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
        self.verification_token = verification_token
        self.verification_token_expiration = verification_token_expiration
        self.failed_login_attempts = failed_login_attempts
        self.account_locked = account_locked
        self.city = city
        self.country = country
        self.work_history = work_history or []
        self.skills = skills or []
        self.saved_jobs = saved_jobs or []
        self.applications = applications or []
        self.is_active = is_active

    def save(self):
        return DynamoDB.put_item('Users', self.to_dict())

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

    def generate_verification_token(self):
        token = secrets.token_urlsafe(32)
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=48)  # Token valid for 24 hours
        self.verification_token = token
        self.verification_token_expiration = expiration.isoformat()
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'verification_token': self.verification_token,
                              'verification_token_expiration': self.verification_token_expiration})
        return token

    @staticmethod
    def verify_account(token):
        response = DynamoDB.scan(
            'Users',
            FilterExpression='verification_token = :token AND is_active = :inactive',
            ExpressionAttributeValues={
                ':token': token,
                ':inactive': False
            }
        )
        if response['Items']:
            user_data = response['Items'][0]
            token_expiration = datetime.datetime.fromisoformat(user_data['verification_token_expiration'])
            if datetime.datetime.utcnow() > token_expiration:
                return False, "Verification token has expired."
            # Activate the user
            DynamoDB.update_item('Users',
                                 {'user_id': user_data['user_id']},
                                 {
                                     'is_active': True,
                                     'verification_token': None,
                                     'verification_token_expiration': None
                                 })
            return True, "Account verified successfully."
        return False, "Invalid verification token."

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

    def add_certification(self, cert_id, url, filename, cert_type):
        cert = {'id': cert_id, 'url': url, 'filename': filename, 'type': cert_type}
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

    def add_work_history(self, job_title, company, description, date_from, date_to):
        work_entry = {
            'id': str(uuid.uuid4()),
            'job_title': job_title,
            'company': company,
            'description': description,
            'date_from': date_from,
            'date_to': date_to
        }
        self.work_history.append(work_entry)
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'work_history': self.work_history})

    def delete_work_history(self, work_id):
        self.work_history = [work for work in self.work_history if work['id'] != work_id]
        DynamoDB.update_item('Users',
                             {'user_id': self.user_id},
                             {'work_history': self.work_history})

    def add_skill(self, skill_text):
        skill_id = str(uuid.uuid4())
        skill = {'id': skill_id, 'skill': skill_text}
        if skill not in self.skills:
            self.skills.append(skill)
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'skills': self.skills})
        return skill_id

    def remove_skill(self, skill_id):
        initial_length = len(self.skills)
        self.skills = [skill for skill in self.skills if skill['id'] != skill_id]
        if len(self.skills) < initial_length:
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'skills': self.skills})
            return True
        return False

    # Method to get user skills
    def get_skills(self):
        return self.skills

    def save_job(self, job_id):
        if job_id not in self.saved_jobs:
            self.saved_jobs.append(job_id)
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'saved_jobs': self.saved_jobs})

    def unsave_job(self, job_id):
        if job_id in self.saved_jobs:
            self.saved_jobs = [job for job in self.saved_jobs if job != job_id]
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'saved_jobs': self.saved_jobs})

    def add_application(self, application_id):
        if application_id not in self.applications:
            self.applications.append(application_id)
            DynamoDB.update_item('Users',
                                 {'user_id': self.user_id},
                                 {'applications': self.applications})

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
            'token_expiration': self.token_expiration,
            'verification_token': self.verification_token,
            'verification_token_expiration': self.verification_token_expiration,
            'failed_login_attempts': self.failed_login_attempts,
            'account_locked': self.account_locked,
            'city': self.city,
            'country': self.country,
            'work_history': self.work_history,
            'skills': self.skills,
            'saved_jobs': self.saved_jobs,
            'applications': self.applications,
            'is_active': self.is_active
        }

    @staticmethod
    def get_all_active_users():
        items = DynamoDB.get_all_active_users()
        return [User(**item) for item in items]

    @staticmethod
    def get_all_users():
        items = DynamoDB.get_all_users()
        return [User(**item) for item in items]

    def update_fields(self, fields):
        try:
            # Handle 'location' separately if present
            if 'location' in fields and fields['location']:
                try:
                    city, country = map(str.strip, fields['location'].split(',', 1))
                    if city and country:
                        self.city = city
                        self.country = country
                except ValueError:
                    pass  # Optionally handle invalid format

            # Update other fields
            for key, value in fields.items():
                if key != 'location' and hasattr(self, key):
                    setattr(self, key, value)
            self.save()
            return True, "User updated successfully."
        except Exception as e:
            print(f"Error updating User: {e}")
            return False, str(e)
