import uuid
import datetime
import json
from flask import request, g
import hmac

from .database_service import DynamoDB

class SessionManager:
    SESSION_TABLE = 'Sessions'
    SESSION_DURATION_HOURS = 24  # Session valid for 24 hours

    @classmethod
    def create_session(cls, user_id, user_type):
        # Remove existing sessions if needed
        cls.remove_existing_sessions(user_id, user_type)

        session_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow()
        expires_at = created_at + datetime.timedelta(hours=cls.SESSION_DURATION_HOURS)

        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'user_type': user_type,  # Store user type
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'data': {}  # Additional session data
        }

        success = DynamoDB.put_item(cls.SESSION_TABLE, session_data)
        if success:
            return session_id
        return None

    @classmethod
    def remove_existing_sessions(cls, user_id, user_type):
        table = DynamoDB.dynamodb.Table(cls.SESSION_TABLE)
        try:
            response = table.scan(
                FilterExpression='user_id = :uid AND user_type = :utype',
                ExpressionAttributeValues={
                    ':uid': user_id,
                    ':utype': user_type
                }
            )
            for item in response.get('Items', []):
                cls.delete_session(item['session_id'])
        except Exception as e:
            print(f"Error removing existing sessions for user {user_id}: {e}")

    @classmethod
    def get_session(cls, session_id):
        item = DynamoDB.get_item(cls.SESSION_TABLE, {'session_id': session_id})
        if item:
            # Check if session has expired
            expires_at = datetime.datetime.fromisoformat(item['expires_at'])
            if datetime.datetime.utcnow() < expires_at:
                return item
            else:
                # Session expired, delete it
                cls.delete_session(session_id)
        return None

    @classmethod
    def delete_session(cls, session_id):
        table = DynamoDB.dynamodb.Table(cls.SESSION_TABLE)
        try:
            table.delete_item(Key={'session_id': session_id})
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    @classmethod
    def update_session_data(cls, session_id, data):
        table = DynamoDB.dynamodb.Table(cls.SESSION_TABLE)
        try:
            table.update_item(
                Key={'session_id': session_id},
                UpdateExpression="SET data = :data",
                ExpressionAttributeValues={':data': json.dumps(data)}
            )
            return True
        except Exception as e:
            print(f"Error updating session data for {session_id}: {e}")
            return False

    @classmethod
    def cleanup_expired_sessions(cls):
        table = DynamoDB.dynamodb.Table(cls.SESSION_TABLE)
        try:
            response = table.scan(
                FilterExpression='expires_at < :now',
                ExpressionAttributeValues={':now': datetime.datetime.utcnow().isoformat()}
            )
            for item in response.get('Items', []):
                cls.delete_session(item['session_id'])
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
