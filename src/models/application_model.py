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

    def _update_status(self, new_status):
        """Instance method to update the status of an application"""
        valid_statuses = ['Pending', 'Accepted', 'Rejected']
        if new_status not in valid_statuses:
            return False

        try:
            success = DynamoDB.update_item(
                'Applications',
                {'application_id': self.application_id},
                update_values={'#s': new_status},
                attribute_names={'#s': 'status'}
            )
            if success:
                self.status = new_status
            return success
        except Exception as e:
            print(f"Error updating application status: {e}")
            return False

    @staticmethod
    def update_status(application_id, new_status):
        """Static method to update application status"""
        application = Application.get_by_id(application_id)
        if application:
            return application._update_status(new_status)
        return False

    @staticmethod
    def get_by_id(application_id):
        """Get application by ID"""
        item = DynamoDB.get_item('Applications', {'application_id': application_id})
        if item:
            return Application(**item)
        return None

    @staticmethod
    def delete_by_application_id(application_id):
        try:
            # Use DynamoDB client to delete the application by application_id
            DynamoDB.delete_item(
                'Applications',
                key={
                    'application_id': application_id
                }
            )
            print(f"Application: {application_id} removed successfully!")
            return True, "Application removed successfully."
        except Exception as e:
            print(f"Error deleting application: {e}")
            return False, "An error occurred while deleting the application."

