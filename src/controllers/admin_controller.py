from ..models.admin_model import Admin
from ..services.email_service import send_reset_email
import bcrypt
import datetime

class AdminController:
    @staticmethod
    def login(email, password):
        admin = Admin.get_by_email(email)
        if admin:
            if admin.account_locked:
                return None, "Account is locked. Please use the 'Forgot Password' option to unlock your account."
            if bcrypt.checkpw(password.encode('utf-8'), admin.password.encode('utf-8')):
                admin.reset_failed_attempts()
                return admin, None
            else:
                admin.increment_failed_attempts()
                if admin.account_locked:
                    return None, "Too many failed attempts. Account is locked. Please use the 'Forgot Password' option to unlock your account."
                return None, "Invalid email or password."
        return None, "Invalid email or password."

    @staticmethod
    def get_admin_by_id(admin_id):
        return Admin.get_by_id(admin_id)

    @staticmethod
    def register_admin(email, password, first_name, last_name):
        # Check if an admin with the given email already exists
        existing_admin = Admin.get_by_email(email)
        if existing_admin:
            return False, "An admin with this email already exists."

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create a new Admin instance
        new_admin = Admin(
            admin_id=None,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )

        # Save the new admin to the database
        new_admin.save()
        return True, "Admin registered successfully."

    @staticmethod
    def reset_password(email):
        admin = Admin.get_by_email(email)
        if admin:
            token = admin.generate_reset_token()
            was_locked = admin.account_locked
            if send_reset_email(email, token, was_locked, role='admin'):
                admin.unlock_account()  # Unlock the account when reset password is requested
                return True, "Reset link sent to your email.", was_locked
            else:
                return False, "Failed to send reset email. Please try again.", was_locked
        return False, "No admin found with this email address.", False

    @staticmethod
    def reset_password_with_token(token, new_password):
        admin = Admin.get_by_reset_token(token)
        if admin:
            if admin.token_expiration and datetime.datetime.utcnow() < datetime.datetime.fromisoformat(admin.token_expiration):
                # Validate the new password
                is_valid, message = AdminController.validate_password(new_password)
                if not is_valid:
                    return False, message, False

                was_locked = admin.account_locked
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                admin.update_password(hashed_password)
                unlock_message = " Your account has been unlocked." if was_locked else ""
                return True, f"Password updated successfully.{unlock_message}", was_locked
            else:
                return False, "Token expired", False
        return False, "Invalid token", False

    @staticmethod
    def validate_password(password):
        import re
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
