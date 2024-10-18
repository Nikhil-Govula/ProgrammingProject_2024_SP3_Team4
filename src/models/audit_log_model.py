import uuid
import datetime

from ..services.database_service import DynamoDB

class AuditLog:
    def __init__(self, admin_id, action, target_user_id, log_id=None, timestamp=None, details=None):
        self.log_id = log_id or str(uuid.uuid4())
        self.admin_id = admin_id
        self.action = action
        self.target_user_id = target_user_id
        self.timestamp = timestamp or datetime.datetime.utcnow().isoformat()
        self.details = details or {}

    def save(self):
        DynamoDB.put_item('AuditLogs', self.to_dict())

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'admin_id': self.admin_id,
            'action': self.action,
            'target_user_id': self.target_user_id,
            'timestamp': self.timestamp,
            'details': self.details
        }

    @staticmethod
    def get_all_logs():
        response = DynamoDB.scan('AuditLogs')
        return response.get('Items', [])

    @staticmethod
    def log_action(admin_id, action, target_user_id, details=None):
        audit_log = AuditLog(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            details=details
        )
        audit_log.save()