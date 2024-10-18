import re
import uuid

import boto3
from botocore.exceptions import ClientError
from dateutil import parser
from werkzeug.utils import secure_filename

from config import Config
from ..models.user_model import User
from ..services.email_service import send_reset_email
import bcrypt
import datetime

class UserController:
    @staticmethod
    def login(email, password):
        user = User.get_by_email(email)
        if user:
            if not user.is_active:
                return None, "This account has been deactivated. Please contact support for assistance."
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

    @staticmethod
    def update_profile(user_id, user_type, first_name, last_name, email, phone_number, profile_picture,
                       location=None, delete_certs=None):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Check if the new email is already taken by another user
        if email != user.email:
            existing_user = User.get_by_email(email)
            if existing_user and existing_user.user_id != user_id:
                return False, "Email is already in use by another account."

        # Handle profile picture update
        if profile_picture:
            new_profile_picture_url, error = UserController.update_profile_picture(user, profile_picture)
            if error:
                return False, error
            user.profile_picture_url = new_profile_picture_url

        # Handle certification deletion if any
        if delete_certs:
            for cert_url in delete_certs:
                user.remove_certification(cert_url)
                UserController.delete_file_from_s3(cert_url)

        # Handle location
        if location:
            # Assuming location is in "City, Country" format
            try:
                city, country = map(str.strip, location.split(',', 1))
                if not city or not country:
                    return False, "Both city and country must be provided in the location."
                user.city = city
                user.country = country
            except ValueError:
                return False, "Invalid location format. Please use 'City, Country'."

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        user.save()
        return True, "Profile updated successfully."

    @staticmethod
    def change_password(user_id, current_password, new_password, confirm_password):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
            return False, "Current password is incorrect."

        # Validate new password
        is_valid, message = UserController.validate_password(new_password)
        if not is_valid:
            return False, message

        if new_password != confirm_password:
            return False, "New passwords do not match."

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.update_password(hashed_password)
        return True, "Password changed successfully."

    @staticmethod
    def allowed_image_file(filename):
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def update_profile_picture(user, profile_picture):
        if not profile_picture or profile_picture.filename == '':
            return user.profile_picture_url, None

        if not UserController.allowed_image_file(profile_picture.filename):
            return None, "Invalid file type. Please upload an image (png, jpg, jpeg, gif, webp)."

        s3 = boto3.client('s3',
                          region_name=Config.S3_REGION,
                          aws_access_key_id=Config.AWS_ACCESS_KEY,
                          aws_secret_access_key=Config.AWS_SECRET_KEY)

        # Delete old profile picture if it exists
        if user.profile_picture_url:
            try:
                old_key = \
                user.profile_picture_url.split(f"{Config.S3_BUCKET_NAME}.s3.{Config.S3_REGION}.amazonaws.com/")[1]
                s3.delete_object(Bucket=Config.S3_BUCKET_NAME, Key=old_key)
            except Exception as e:
                print(f"Error deleting old profile picture: {e}")

        # Upload new profile picture
        folder_name = "ProgrammingProject_data/user_data/profile_pictures"
        filename = secure_filename(profile_picture.filename)
        unique_filename = f"{folder_name}/{user.user_id}_{uuid.uuid4().hex}_{filename}"

        try:
            s3.upload_fileobj(
                profile_picture,
                Config.S3_BUCKET_NAME,
                unique_filename,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': profile_picture.content_type
                }
            )
            new_profile_picture_url = f"https://{Config.S3_BUCKET_NAME}.s3.{Config.S3_REGION}.amazonaws.com/{unique_filename}"
            return new_profile_picture_url, None
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None, "Failed to upload profile picture. Please try again."


    @staticmethod
    def allowed_certification_file(filename):
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'docx', 'doc'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def upload_certification(user, certification_file, cert_type):
        s3 = boto3.client('s3',
                          region_name=Config.S3_REGION,
                          aws_access_key_id=Config.AWS_ACCESS_KEY,
                          aws_secret_access_key=Config.AWS_SECRET_KEY)

        folder_name = "ProgrammingProject_data/user_data/certifications"
        filename = secure_filename(certification_file.filename)
        unique_filename = f"{folder_name}/{user.user_id}_{uuid.uuid4().hex}_{filename}"

        try:
            s3.upload_fileobj(
                certification_file,
                Config.S3_BUCKET_NAME,
                unique_filename,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': certification_file.content_type
                }
            )
            cert_url = f"https://{Config.S3_BUCKET_NAME}.s3.{Config.S3_REGION}.amazonaws.com/{unique_filename}"
            cert_id = str(uuid.uuid4())
            user.add_certification(cert_id, cert_url, filename, cert_type)
            return cert_url, filename, cert_id, None
        except ClientError as e:
            print(f"Error uploading certification to S3: {e}")
            return None, None, None, "Failed to upload certification. Please try again."

    @staticmethod
    def delete_certification(user_id, cert_url):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Extract the key from the URL
        try:
            key = cert_url.split(f"{Config.S3_BUCKET_NAME}.s3.{Config.S3_REGION}.amazonaws.com/")[1]
        except IndexError:
            return False, "Invalid certification URL."

        s3 = boto3.client('s3',
                          region_name=Config.S3_REGION,
                          aws_access_key_id=Config.AWS_ACCESS_KEY,
                          aws_secret_access_key=Config.AWS_SECRET_KEY)

        try:
            s3.delete_object(Bucket=Config.S3_BUCKET_NAME, Key=key)
            user.remove_certification(cert_url)
            user.save()
            return True
        except ClientError as e:
            print(f"Error deleting certification from S3: {e}")
            return False

    @staticmethod
    def update_profile_field(user_id, field, value):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Specific validations per field
        if field == 'email':
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
                return False, "Invalid email format."

            # Check if the new email is already taken by another user
            existing_user = User.get_by_email(value)
            if existing_user and existing_user.user_id != user_id:
                return False, "Email is already in use by another account."

        elif field == 'phone_number':
            # Simple phone number validation (adjust regex as needed)
            if not re.match(r"^\+?1?\d{9,15}$", value):
                return False, "Invalid phone number format."

        elif field in {'first_name', 'last_name'}:
            if not value.strip():
                return False, f"{field.replace('_', ' ').capitalize()} cannot be empty."


        elif field == 'location':
            # Split the location into city and country
            try:
                city, country = value.split(',')
                city = city.strip()
                country = country.strip()
            except ValueError:
                return False, "Invalid location format. Please use 'City, Country'."

            if not city or not country:
                return False, "Both city and country must be provided."

            user.city = city
            user.country = country
        else:
            return False, "Invalid field."

            # Update the field
        if field != 'location':  # location is handled separately
            setattr(user, field, value)
        user.save()
        return True, f"{field.replace('_', ' ').capitalize()} updated successfully."

    @staticmethod
    def add_work_history(user_id, job_title, company, description, date_from, date_to):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Basic validation
        if not all([job_title, company, date_from]):
            return False, "Job Title, Company, and Date From are required."

        user.add_work_history(job_title, company, description, date_from, date_to)
        return True, "Work history added successfully."

    @staticmethod
    def delete_work_history(user_id, work_id):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        # Check if the work_id exists
        work_entry = next((work for work in user.work_history if work['id'] == work_id), None)
        if not work_entry:
            return False, "Work history entry not found."

        user.delete_work_history(work_id)
        return True, "Work history deleted successfully."

    @staticmethod
    def get_user_by_id(user_id):
        return User.get_by_id(user_id)

    @staticmethod
    def add_skill(user_id, skill_text):
        if not skill_text or not skill_text.strip():
            return False, "Skill cannot be empty."

        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        skill_id = user.add_skill(skill_text.strip())
        if skill_id:
            return True, {"id": skill_id, "skill": skill_text.strip()}, None
        else:
            return False, "Skill already exists.", None

    @staticmethod
    def delete_skill(user_id, skill_id):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        success = user.remove_skill(skill_id)
        if success:
            return True, "Skill deleted successfully.", None
        else:
            return False, "Skill not found.", None