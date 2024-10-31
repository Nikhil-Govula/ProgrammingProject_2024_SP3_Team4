# src/models/application_model.py

import uuid
import datetime
from ..services.database_service import DynamoDB

class Application:
    def __init__(self, user_id, job_id, application_id=None, status='Pending', date_applied=None):
        self.application_id = application_id or str(uuid.uuid4())
        self.user_id = user_id
        self.job_id = job_id
        self.status = status
        self.date_applied = date_applied or datetime.datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'application_id': self.application_id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'status': self.status,
            'date_applied': self.date_applied
        }

    def save(self):
        try:
            DynamoDB.put_item('Applications', self.to_dict())
            return True, "Application submitted successfully."
        except Exception as e:
            print(f"Error saving application: {e}")
            return False, "An error occurred while submitting your application."

    @staticmethod
    def get_by_id(application_id):
        item = DynamoDB.get_item('Applications', {'application_id': application_id})
        if item:
            return Application(**item)
        return None

    @staticmethod
    def get_by_user_id(user_id):
        response = DynamoDB.scan(
            'Applications',
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        return [Application(**item) for item in response['Items']]

    @staticmethod
    def get_by_user_and_job(user_id, job_id):
        try:
            response = DynamoDB.scan(
                'Applications',
                FilterExpression='user_id = :uid AND job_id = :jid',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':jid': job_id
                }
            )
            items = response.get('Items', [])
            if items:
                return Application(**items[0])
            return None
        except Exception as e:
            print(f"Error checking application: {e}")
            return None