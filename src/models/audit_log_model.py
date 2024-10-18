import uuid
import datetime

from ..services.database_service import DynamoDB

class AuditLog:
    def __init__(self, admin_id, admin_email, action, target_user_id, target_user_email=None, log_id=None, timestamp=None, details=None):
        self.log_id = log_id or str(uuid.uuid4())
        self.admin_id = admin_id
        self.admin_email = admin_email  # Existing field
        self.action = action
        self.target_user_id = target_user_id
        self.target_user_email = target_user_email  # New field
        self.timestamp = timestamp or datetime.datetime.utcnow().isoformat()
        self.details = details or {}

    def save(self):
        DynamoDB.put_item('AuditLogs', self.to_dict())

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'admin_id': self.admin_id,
            'admin_email': self.admin_email,  # Existing field
            'action': self.action,
            'target_user_id': self.target_user_id,
            'target_user_email': self.target_user_email,  # Include in the dictionary
            'timestamp': self.timestamp,
            'details': self.details
        }

    @staticmethod
    def get_all_logs():
        response = DynamoDB.scan('AuditLogs')
        logs = response.get('Items', [])

        # Sort logs by timestamp in descending order
        logs.sort(key=lambda log: log['timestamp'], reverse=True)

        return logs

    @staticmethod
    def log_action(admin_id, admin_email, action, target_user_id, target_user_email=None, details=None):
        audit_log = AuditLog(
            admin_id=admin_id,
            admin_email=admin_email,
            action=action,
            target_user_id=target_user_id,
            target_user_email=target_user_email,  # Pass the target_user_email
            details=details
        )
        audit_log.save()
