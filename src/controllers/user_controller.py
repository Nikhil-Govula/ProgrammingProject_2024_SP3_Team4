from dateutil import parser

from ..models.user_model import User
from ..services.email_service import send_reset_email
import bcrypt
import datetime

class UserController:
    @staticmethod
    def login(email, password):
        user = User.get_by_email(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
        return None

    @staticmethod
    def reset_password(email):
        user = User.get_by_email(email)
        if user:
            token = user.generate_reset_token()
            if send_reset_email(email, token):
                return True, "Reset link sent to your email."
            else:
                return False, "Failed to send reset email. Please try again."
        return False, "No user found with this email address."

    @staticmethod
    def reset_password_with_token(token, new_password):
        user = User.get_by_reset_token(token)
        if user:
            if datetime.datetime.utcnow() < parser.parse(user.token_expiration):
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.update_password(hashed_password.decode('utf-8'))
                return True, "Password updated successfully"
            else:
                return False, "Token expired"
        return False, "Invalid token"