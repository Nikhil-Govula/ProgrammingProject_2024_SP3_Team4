import re

from dateutil import parser

from ..models.user_model import User
from ..services.email_service import send_reset_email
import bcrypt
import datetime

class UserController:
    @staticmethod
    def login(email, password):
        user = User.get_by_email(email)
        if user:
            if user.account_locked:
                return None, "Account is locked. Please use the 'Forgot Password' option to unlock your account."
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                user.reset_failed_attempts()
                user.unlock_account()
                return user, None
            else:
                user.increment_failed_attempts()
                if user.account_locked:
                    return None, "Too many failed attempts. Account is locked. Please use the 'Forgot Password' option to unlock your account."
                return None, "Invalid email or password."
        return None, "Invalid email or password."

    @staticmethod
    def reset_password(email):
        user = User.get_by_email(email)
        if user:
            token = user.generate_reset_token()
            was_locked = user.account_locked
            if send_reset_email(email, token, was_locked):
                user.unlock_account()  # Unlock the account when reset password is requested
                return True, "Reset link sent to your email.", was_locked
            else:
                return False, "Failed to send reset email. Please try again.", was_locked
        return False, "No user found with this email address.", False

    @staticmethod
    def reset_password_with_token(token, new_password):
        user = User.get_by_reset_token(token)
        if user:
            if datetime.datetime.utcnow() < parser.parse(user.token_expiration):
                # Validate the new password
                is_valid, message = UserController.validate_password(new_password)
                if not is_valid:
                    return False, message, False

                was_locked = user.account_locked
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.update_password(hashed_password.decode('utf-8'))
                user.unlock_account()  # Ensure the account is unlocked when password is reset
                unlock_message = " Your account has been unlocked." if was_locked else ""
                return True, f"Password updated successfully.{unlock_message}", was_locked
            else:
                return False, "Token expired", False
        return False, "Invalid token", False

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter."

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter."

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number."

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character."

        return True, "Password meets all requirements."

    @staticmethod
    def register_user(email, password, first_name, last_name, phone_number):
        # Validate the password
        is_valid, message = UserController.validate_password(password)
        if not is_valid:
            return False, message

        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            return False, "A user with this email already exists."

        # Create new user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(
            user_id=None,  # Will be generated automatically
            email=email,
            password=hashed_password.decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )
        new_user.save()
        return True, "User registered successfully."