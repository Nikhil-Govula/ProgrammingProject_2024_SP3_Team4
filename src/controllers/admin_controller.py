import logging

from flask import g

from .user_controller import UserController
from ..models.admin_model import Admin
from ..models.user_model import User
from ..models.employer_model import Employer
from ..services.email_service import send_reset_email
from ..models.audit_log_model import AuditLog
import bcrypt
import datetime

class AdminController:
    @staticmethod
    def login(email, password):
        admin = Admin.get_by_email(email)
        if admin:
            if not admin.is_active:
                return None, "This account has been deactivated. Please contact support for assistance."
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

    @staticmethod
    def create_account(email, password, first_name, last_name, account_type):
        # Check if email already exists in Users or Admins
        existing_user = User.get_by_email(email)
        existing_admin = Admin.get_by_email(email)
        if existing_user or existing_admin:
            return False, "An account with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if account_type.lower() == 'admin':
            new_admin = Admin(
                admin_id=None,  # This will be auto-generated
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name
            )
            new_admin.save()
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action='create_admin',
                target_user_id=new_admin.admin_id,
                target_user_email=new_admin.email,  # Pass the target_user_email
                details={'email': email}
            )
            return True, "Admin account created successfully."

        elif account_type.lower() == 'employee':
            new_user = User(
                user_id=None,  # This will be auto-generated
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                phone_number=''  # Default or handle accordingly
            )
            new_user.save()
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action='create_user',
                target_user_id=new_user.user_id,
                target_user_email=new_user.email,  # New parameter
                details={'email': email}
            )

            return True, "User account created successfully."

        else:
            return False, "Invalid account type."

    @staticmethod
    def get_all_accounts(account_type=None, account_status=None, search_query=None):
        accounts = []

        # Fetch Admins, Employers, and Users based on account_type
        if account_type is None or account_type.lower() == 'admin':
            admins = Admin.get_all_admins()
            accounts.extend(admins)

        if account_type is None or account_type.lower() == 'employer':
            employers = Employer.get_all_employers()
            accounts.extend(employers)

        if account_type is None or account_type.lower() == 'user':
            users = User.get_all_users()
            accounts.extend(users)

        # Apply Account Status Filter
        if account_status:
            filtered_accounts = []
            for acc in accounts:
                if ('active' in account_status and acc.is_active and not acc.account_locked) or \
                        ('locked' in account_status and acc.account_locked) or \
                        ('archived' in account_status and not acc.is_active and not acc.account_locked):
                    filtered_accounts.append(acc)
            accounts = filtered_accounts

        # Apply Search Filter
        if search_query:
            search_query = search_query.lower()
            accounts = [acc for acc in accounts if
                        search_query in acc.email.lower() or
                        search_query in getattr(acc, 'first_name', '').lower() or
                        search_query in getattr(acc, 'last_name', '').lower() or
                        search_query in getattr(acc, 'company_name', '').lower()]

        return accounts

    @staticmethod
    def get_account_by_id(account_id, account_type):
        if account_type.lower() == 'admin':
            return Admin.get_by_id(account_id)
        elif account_type.lower() == 'employer':
            return Employer.get_by_id(account_id)
        elif account_type.lower() == 'user':
            return User.get_by_id(account_id)
        else:
            return None

    @staticmethod
    def update_account(account_id, account_type, **kwargs):
        """
        Update specific fields of an account based on account_type.
        """
        if account_type.lower() == 'admin':
            account = Admin.get_by_id(account_id)
        elif account_type.lower() == 'employer':
            account = Employer.get_by_id(account_id)
        elif account_type.lower() == 'user':
            account = User.get_by_id(account_id)
        else:
            return False, "Invalid account type."

        if not account:
            return False, f"{account_type.capitalize()} not found."

        # Handle password hashing if password is being updated
        if 'password' in kwargs:
            new_password = kwargs.pop('password')
            is_valid, message = AdminController.validate_password(new_password)
            if not is_valid:
                return False, message
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            kwargs['password'] = hashed_password

        # Handle location for users
        if account_type.lower() == 'user' and 'location' in kwargs:
            location = kwargs.pop('location')
            try:
                city, country = map(str.strip, location.split(',', 1))
                kwargs['city'] = city
                kwargs['country'] = country
            except ValueError:
                return False, "Invalid location format. Use 'City, Country'."

        # **Redact Password Before Logging**
        redacted_update_fields = kwargs.copy()
        if 'password' in redacted_update_fields:
            redacted_update_fields['password'] = '[REDACTED]'

        # Perform the update
        success, message = account.update_fields(kwargs)
        if success:
            # Log the update action with redacted fields
            target_email = getattr(account, 'email', None)
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action=f'update_{account_type}',
                target_user_id=account_id,
                target_user_email=target_email,
                details=redacted_update_fields
            )
            return True, f"{account_type.capitalize()} account updated successfully."
        else:
            return False, "Failed to update account."

    @staticmethod
    def deactivate_account(account_id, account_type):
        if account_type.lower() == 'admin':
            admin = Admin.get_by_id(account_id)
            if not admin:
                return False, "Admin not found."
            admin.is_active = False
            admin.save()
            target_email = AdminController.get_target_user_email(account_type, account_id)
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action=f'deactivate_{account_type}',  # or corresponding action
                target_user_id=admin.admin_id,
                target_user_email=target_email,  # New parameter
                details={}
            )
            return True, "Admin account deactivated successfully."

        elif account_type.lower() == 'employer':
            employer = Employer.get_by_id(account_id)
            if not employer:
                return False, "Employer not found."
            employer.is_active = False
            employer.save()
            target_email = AdminController.get_target_user_email(account_type, account_id)
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action=f'deactivate_{account_type}',  # or corresponding action
                target_user_id=employer.employer_id,
                target_user_email=target_email,  # New parameter
                details={}
            )
            return True, "Employer account deactivated successfully."

        elif account_type.lower() == 'user':
            user = User.get_by_id(account_id)
            if not user:
                return False, "User not found."
            user.is_active = False
            user.save()
            target_email = AdminController.get_target_user_email(account_type, account_id)
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action=f'deactivate_{account_type}',  # or corresponding action
                target_user_id=user.user_id,
                target_user_email=target_email,  # New parameter
                details={}
            )
            return True, "User account deactivated successfully."

        else:
            return False, "Invalid account type."

    @staticmethod
    def create_user_account(email, password, first_name, last_name, phone_number, location, skills):
        logging.info("Creating user account for email: %s", email)
        existing_user = User.get_by_email(email)
        if existing_user:
            logging.warning("User account creation failed: Email %s already exists.", email)
            return False, "A user with this email already exists."

        # Process location
        try:
            city, country = map(str.strip, location.split(',', 1)) if ',' in location else ('', '')
        except ValueError:
            logging.error("Invalid location format: %s", location)
            return False, "Location must be in the format 'City, Country'."

        # Hash the password
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception as e:
            logging.exception("Error hashing password for user: %s", email)
            return False, "Password processing failed."

        # Create a new User instance
        new_user = User(
            user_id=None,  # Auto-generated
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            city=city,
            country=country
        )

        # Save the new user to the database
        success = new_user.save()
        if not success:
            logging.error("Failed to save user account for email: %s", email)
            return False, "Failed to create user account due to a database error."

        # Add skills
        for skill in skills:
            new_user.add_skill(skill.strip())

        # Log the creation in AuditLog
        try:
            details = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'location': location,
                'skills': skills
            }

            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action='create_user',
                target_user_id=new_user.user_id,
                target_user_email=new_user.email,
                details=details
            )
        except Exception as e:
            logging.exception("Failed to log audit action for user creation.")

        logging.info("User account created successfully for email: %s", email)
        return True, "User account created successfully."

    @staticmethod
    def create_employer_account(email, password, company_name, contact_person, phone_number):
        existing_employer = Employer.get_by_email(email)
        if existing_employer:
            return False, "An employer with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_employer = Employer(
            employer_id=None,  # This will be auto-generated
            email=email,
            password=hashed_password,
            company_name=company_name,
            contact_person=contact_person,
            phone_number=phone_number
        )
        new_employer.save()

        # Log full details of the employer creation
        details = {
            'email': email,
            'company_name': company_name,
            'contact_person': contact_person,
            'phone_number': phone_number
        }

        AuditLog.log_action(
            admin_id=g.user.admin_id,
            admin_email=g.user.email,
            action='create_employer',
            target_user_id=new_employer.employer_id,
            target_user_email=new_employer.email,  # New parameter
            details=details  # Include full details
        )
        return True, "Employer account created successfully."

    @staticmethod
    def create_admin_account(email, password, first_name, last_name):
        logging.info("Creating admin account for email: %s", email)
        existing_admin = Admin.get_by_email(email)
        if existing_admin:
            logging.warning("Admin account creation failed: Email %s already exists.", email)
            return False, "An admin with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_admin = Admin(
            admin_id=None,  # This will be auto-generated
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )

        success = new_admin.save()
        if not success:
            logging.error("Failed to save admin account for email: %s", email)
            return False, "Failed to create admin account due to a database error."

        # Log full details of the admin creation
        details = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }

        AuditLog.log_action(
            admin_id=g.user.admin_id,
            admin_email=g.user.email,
            action='create_admin',
            target_user_id=new_admin.admin_id,
            target_user_email=new_admin.email,  # New parameter
            details=details  # Include full details
        )
        logging.info("Admin account created successfully for email: %s", email)
        return True, "Admin account created successfully."

    @staticmethod
    def toggle_account_lock(account_id, account_type):
        account = AdminController.get_account_by_id(account_id, account_type)
        if account:
            action = ''
            if account_type.lower() == 'admin':
                if account.account_locked:
                    account.unlock_account()
                    action = 'unlock_admin'
                    message = "Admin account unlocked successfully."
                else:
                    account.lock_account()
                    action = 'lock_admin'
                    message = "Admin account locked successfully."
            elif account_type.lower() == 'user':
                if account.account_locked:
                    account.unlock_account()
                    action = 'unlock_user'
                    message = "User account unlocked successfully."
                else:
                    account.lock_account()
                    action = 'lock_user'
                    message = "User account locked successfully."
            elif account_type.lower() == 'employer':
                if account.account_locked:
                    account.unlock_account()
                    action = 'unlock_employer'
                    message = "Employer account unlocked successfully."
                else:
                    account.lock_account()
                    action = 'lock_employer'
                    message = "Employer account locked successfully."
            else:
                return False, "Invalid account type."

            # Log the lock/unlock action
            target_email = getattr(account, 'email', None)
            AuditLog.log_action(
                admin_id=g.user.admin_id,
                admin_email=g.user.email,
                action=action,
                target_user_id=account_id,
                target_user_email=target_email,  # Logging the target user email
                details={'action': action, 'account_id': account_id}
            )

            return True, message
        return False, f"{account_type.capitalize()} not found."

    @staticmethod
    def toggle_account_activation(account_id, account_type):
        account = AdminController.get_account_by_id(account_id, account_type)
        if not account:
            print(f"Account not found: {account_type} {account_id}")  # Debug log
            return False, f"{account_type.capitalize()} not found."

        print(f"Before toggle: {account_type} {account_id} is_active = {account.is_active}")  # Debug log

        if account_type.lower() == 'employer':
            account.toggle_active_status()
        else:
            account.is_active = not account.is_active
            account.save()

        print(f"After toggle: {account_type} {account_id} is_active = {account.is_active}")  # Debug log

        # Prepare log details
        action = 'activate' if account.is_active else 'deactivate'
        target_email = account.email if hasattr(account, 'email') else None
        log_details = {
            'action': action,
            'account_id': account_id,
            'is_active': account.is_active
        }

        # Log the action
        AuditLog.log_action(
            admin_id=g.user.admin_id,
            admin_email=g.user.email,
            action=f'{action}_{account_type}',
            target_user_id=account_id,
            target_user_email=target_email,  # New parameter
            details=log_details  # Include relevant details
        )

        return True, f"{account_type.capitalize()} account {'activated' if account.is_active else 'deactivated'} successfully."

    @staticmethod
    def get_target_user_email(account_type, account_id):
        if account_type.lower() == 'admin':
            admin = Admin.get_by_id(account_id)
            return admin.email if admin else None
        elif account_type.lower() == 'employer':
            employer = Employer.get_by_id(account_id)
            return employer.email if employer else None
        elif account_type.lower() == 'user':
            user = User.get_by_id(account_id)
            return user.email if user else None
        else:
            return None
