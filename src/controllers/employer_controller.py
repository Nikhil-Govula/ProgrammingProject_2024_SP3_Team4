# src/controllers/employer_controller.py

from ..models.employer_model import Employer
from ..controllers.user_controller import UserController  # For password validation
from ..services.email_service import send_reset_email
import bcrypt
import datetime

class EmployerController:
    @staticmethod
    def login(email, password):
        employer = Employer.get_by_email(email)
        if employer:
            if not employer.is_active:
                return None, "This account has been deactivated. Please contact support for assistance."
            if employer.account_locked:
                return None, "Account is locked. Please use the 'Forgot Password' option to unlock your account."
            if bcrypt.checkpw(password.encode('utf-8'), employer.password.encode('utf-8')):
                employer.reset_failed_attempts()
                return employer, None
            else:
                employer.increment_failed_attempts()
                if employer.account_locked:
                    return None, "Too many failed attempts. Account is locked. Please use the 'Forgot Password' option to unlock your account."
                return None, "Invalid email or password."
        return None, "Invalid email or password."

    @staticmethod
    def register_employer(email, password, company_name, contact_person, phone_number):
        existing_employer = Employer.get_by_email(email)
        if existing_employer:
            return False, "An employer with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_employer = Employer(
            employer_id=None,  # This will be generated automatically
            company_name=company_name,
            email=email,
            password=hashed_password,
            contact_person=contact_person,
            phone_number=phone_number
        )
        new_employer.save()
        return True, "Employer registered successfully."

    @staticmethod
    def reset_password(email):
        employer = Employer.get_by_email(email)
        if employer:
            token = employer.generate_reset_token()
            was_locked = employer.account_locked
            if send_reset_email(email, token, was_locked, role='employer'):
                employer.unlock_account()  # Unlock the account when reset password is requested
                return True, "Reset link sent to your email.", was_locked
            else:
                return False, "Failed to send reset email. Please try again.", was_locked
        return False, "No employer found with this email address.", False

    @staticmethod
    def reset_password_with_token(token, new_password):
        employer = Employer.get_by_reset_token(token)
        if employer:
            if employer.token_expiration and datetime.datetime.utcnow() < datetime.datetime.fromisoformat(employer.token_expiration):
                # Validate the new password
                is_valid, message = UserController.validate_password(new_password)  # Reuse user password validation
                if not is_valid:
                    return False, message, False

                was_locked = employer.account_locked
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                employer.update_password(hashed_password)
                unlock_message = " Your account has been unlocked." if was_locked else ""
                return True, f"Password updated successfully.{unlock_message}", was_locked
            else:
                return False, "Token expired", False
        return False, "Invalid token", False
