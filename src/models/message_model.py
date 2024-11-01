from datetime import datetime, timezone
import uuid
from ..services.database_service import DynamoDB


class Message:
    def __init__(self, message_id=None, sender_id=None, receiver_id=None,
                 sender_type=None, content=None, timestamp=None, is_read=False,
                 job_id=None):
        self.message_id = message_id or str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sender_type = sender_type
        self.content = content

        # Use UTC time with timezone information
        if timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        else:
            self.timestamp = timestamp

        self.is_read = is_read
        self.job_id = job_id

    def save(self):
        return DynamoDB.put_item('Messages', self.to_dict())

    @staticmethod
    def get_conversation(user_id, employer_id, job_id=None):
        response = DynamoDB.scan(
            'Messages',
            FilterExpression=(
                '(sender_id = :user_id AND receiver_id = :employer_id) OR '
                '(sender_id = :employer_id AND receiver_id = :user_id)'
            ),
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':employer_id': employer_id
            }
        )

        messages = [Message(**item) for item in response.get('Items', [])]
        if job_id:
            messages = [m for m in messages if m.job_id == job_id]

        # Sort messages in ascending order (oldest first)
        return sorted(messages, key=lambda x: x.timestamp)

    def mark_as_read(self):
        self.is_read = True
        DynamoDB.update_item(
            'Messages',
            {'message_id': self.message_id},
            {'is_read': True}
        )

    @staticmethod
    def get_unread_count(user_id, user_type):
        response = DynamoDB.scan(
            'Messages',
            FilterExpression='receiver_id = :user_id AND is_read = :is_read',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':is_read': False
            }
        )
        return len(response.get('Items', []))

    @staticmethod
    def get_new_messages(user_id, last_check, user_type=None):
        """
        Get new messages, properly handling sender_type for both users and employers.

        Args:
            user_id: The ID of the user/employer
            last_check: Timestamp to check messages after
            user_type: Type of the user ('user' or 'employer')
        """
        response = DynamoDB.scan(
            'Messages',
            FilterExpression='(sender_id = :user_id OR receiver_id = :user_id) AND #ts > :last_check',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':last_check': last_check
            },
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            }
        )

        messages = []
        for item in response.get('Items', []):
            message = Message(**item)
            # If this message was sent by the current user, ensure sender_type is correct
            if message.sender_id == user_id:
                message.sender_type = user_type
            messages.append(message)

        return messages

    def to_dict(self):
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_type': self.sender_type,
            'content': self.content,
            'timestamp': self.timestamp,
            'is_read': self.is_read,
            'job_id': self.job_id
        }