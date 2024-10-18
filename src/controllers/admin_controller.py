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
            AuditLog.log_action(admin_id=g.user.admin_id, action='create_admin', target_user_id=new_admin.admin_id,
                                details={'email': email})
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
            AuditLog.log_action(admin_id=g.user.admin_id, action='create_user', target_user_id=new_user.user_id,
                                details={'email': email})
            return True, "User account created successfully."

        else:
            return False, "Invalid account type."

    @staticmethod
    def get_all_accounts(account_type=None, account_status='all', search_query=None):
        accounts = []

        # Fetch Admins
        if account_type is None or account_type.lower() == 'admin':
            admins = Admin.get_all_admins()
            accounts.extend(admins)

        # Fetch Employers
        if account_type is None or account_type.lower() == 'employer':
            employers = Employer.get_all_employers()
            accounts.extend(employers)

        # Fetch Users
        if account_type is None or account_type.lower() == 'user':
            users = User.get_all_users()
            accounts.extend(users)

        # Apply Account Status Filter
        if account_status == 'active':
            accounts = [acc for acc in accounts if acc.is_active and not acc.account_locked]
        elif account_status == 'locked':
            accounts = [acc for acc in accounts if acc.account_locked]
        # When account_status is 'all', we don't filter, showing all accounts

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

        # Prepare the fields to update based on account type
        update_fields = {}
        if account_type.lower() in ['admin', 'user']:
            update_fields['first_name'] = kwargs.get('first_name')
            update_fields['last_name'] = kwargs.get('last_name')

        update_fields['email'] = kwargs.get('email')
        update_fields['phone_number'] = kwargs.get('phone_number')

        if account_type.lower() == 'user':
            update_fields['location'] = kwargs.get('location')
        elif account_type.lower() == 'employer':
            update_fields['company_name'] = kwargs.get('company_name')
            update_fields['contact_person'] = kwargs.get('contact_person')

        # Handle password update
        password = kwargs.get('password')
        if password:
            # Validate password if necessary
            is_valid, message = UserController.validate_password(password)
            if not is_valid:
                return False, message
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            update_fields['password'] = hashed_password

        # Perform the update
        success, message = account.update_fields(update_fields)
        if success:
            # Log the update action
            AuditLog.log_action(admin_id=g.user.admin_id, action=f'update_{account_type}', target_user_id=account_id,
                                details=update_fields)
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
            AuditLog.log_action(admin_id=g.user.admin_id, action='deactivate_admin', target_user_id=admin.admin_id,
                                details={})
            return True, "Admin account deactivated successfully."

        elif account_type.lower() == 'employer':
            employer = Employer.get_by_id(account_id)
            if not employer:
                return False, "Employer not found."
            employer.is_active = False
            employer.save()
            AuditLog.log_action(admin_id=g.user.admin_id, action='deactivate_employer', target_user_id=employer.employer_id,
                                details={})
            return True, "Employer account deactivated successfully."

        elif account_type.lower() == 'user':
            user = User.get_by_id(account_id)
            if not user:
                return False, "User not found."
            user.is_active = False
            user.save()
            AuditLog.log_action(admin_id=g.user.admin_id, action='deactivate_user', target_user_id=user.user_id, details={})
            return True, "User account deactivated successfully."

        else:
            return False, "Invalid account type."

    @staticmethod
    def create_user_account(email, password, first_name, last_name, phone_number, location, skills):
        existing_user = User.get_by_email(email)
        if existing_user:
            return False, "A user with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        city, country = location.split(',') if ',' in location else ('', '')

        new_user = User(
            user_id=None,  # This will be auto-generated
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            city=city.strip(),
            country=country.strip()
        )
        new_user.save()

        # Add skills
        for skill in skills:
            new_user.add_skill(skill.strip())

        AuditLog.log_action(admin_id=g.user.admin_id, action='create_user', target_user_id=new_user.user_id,
                            details={'email': email})
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

        AuditLog.log_action(admin_id=g.user.admin_id, action='create_employer', target_user_id=new_employer.employer_id,
                            details={'email': email, 'company_name': company_name})
        return True, "Employer account created successfully."

    @staticmethod
    def create_admin_account(email, password, first_name, last_name):
        existing_admin = Admin.get_by_email(email)
        if existing_admin:
            return False, "An admin with this email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_admin = Admin(
            admin_id=None,  # This will be auto-generated
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )
        new_admin.save()

        AuditLog.log_action(admin_id=g.user.admin_id, action='create_admin', target_user_id=new_admin.admin_id,
                            details={'email': email})
        return True, "Admin account created successfully."

    @staticmethod
    def toggle_account_lock(account_id, account_type):
        account = AdminController.get_account_by_id(account_id, account_type)
        if account:
            if account_type.lower() == 'admin':
                if account.account_locked:
                    account.unlock_account()
                    message = "Admin account unlocked successfully."
                else:
                    account.lock_account()
                    message = "Admin account locked successfully."
            elif account_type.lower() == 'user':
                if account.account_locked:
                    account.unlock_account()
                    message = "User account unlocked successfully."
                else:
                    account.lock_account()
                    message = "User account locked successfully."
            elif account_type.lower() == 'employer':
                if account.account_locked:
                    account.unlock_account()
                    message = "Employer account unlocked successfully."
                else:
                    account.lock_account()
                    message = "Employer account locked successfully."
            else:
                return False, "Invalid account type."
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

        # Log the action
        action = 'activate' if account.is_active else 'deactivate'
        AuditLog.log_action(admin_id=g.user.admin_id, action=f'{action}_{account_type}', target_user_id=account_id,
                            details={})

        return True, f"{account_type.capitalize()} account {'activated' if account.is_active else 'deactivated'} successfully."


