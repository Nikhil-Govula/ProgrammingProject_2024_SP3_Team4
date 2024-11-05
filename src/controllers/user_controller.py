import re
import uuid

import boto3
from botocore.exceptions import ClientError
from dateutil import parser
from flask import url_for
from werkzeug.utils import secure_filename

from config import Config
from ..models.user_model import User
from ..models.job_model import Job
from ..models.application_model import Application
from ..services import DynamoDB
from ..services.email_service import send_reset_email, send_verification_email
import bcrypt
import datetime


class UserController:
    @staticmethod
    def login(email, password):
        user = User.get_by_email(email)
        if user:
            if not user.is_active:
                # Generate a new verification token
                token = user.generate_verification_token()

                # Generate the full verification link
                verification_link = url_for('user_views.verify_account', token=token, _external=True)

                # Send verification email
                email_sent = send_verification_email(user.email, verification_link, role='user')

                if email_sent:
                    return None, (
                        "Your account is not active. A new verification link has been sent to your email. "
                        "Please verify your account before logging in."
                    )
                else:
                    return None, "Your account is not active and failed to send a new verification email. Please try again later."

            if user.account_locked:
                return None, "Account is locked. Please use the 'Forgot Password' option to unlock your account."

            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                user.reset_failed_attempts()
                user.unlock_account()  # Unlock account on successful login
                return user, None
            else:
                user.increment_failed_attempts()
                if user.account_locked:
                    return None, (
                        "Too many failed attempts. Account is locked. Please use the 'Forgot Password' option to unlock your account."
                    )
                return None, "Invalid email or password."
        return None, "Invalid email or password."

    @staticmethod
    def resend_verification_email(email):
        user = User.get_by_email(email)
        if user:
            if user.is_active:
                return False, "Account is already active. You can log in directly."

            # Generate a new verification token
            verification_token = user.generate_verification_token()

            # Send verification email
            verification_link = url_for('user_views.verify_account', token=verification_token, _external=True)
            email_sent = send_verification_email(email, verification_link)

            if email_sent:
                return True, "A new verification link has been sent to your email."
            else:
                return False, "Failed to send verification email. Please try again later."
        return False, "No account found with this email address."

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

        # Create new user with is_active=False
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(
            user_id=None,  # Will be generated automatically
            email=email,
            password=hashed_password.decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_active=False  # User is inactive until email verification
        )
        new_user.save()

        # Generate verification token
        verification_token = new_user.generate_verification_token()

        # Send verification email
        verification_link = url_for('user_views.verify_account', token=verification_token, _external=True)
        email_sent = send_verification_email(email, verification_link)

        if email_sent:
            return True, "Registration successful! Please check your email to verify your account."
        else:
            return False, "Registration successful, but failed to send verification email. Please contact support."

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

    @staticmethod
    def get_all_active_jobs():
        """
        Retrieve all active jobs from the database.
        """
        return Job.get_all_active_jobs()

    @staticmethod
    def get_job_by_id(job_id):
        """
        Retrieve a specific job by its ID.
        """
        return Job.get_by_id(job_id)

    @staticmethod
    def has_applied_for_job(user_id, job_id):
        """
        Check if a user has already applied for a specific job.
        """
        # Add debug logging
        print(f"Checking application for user {user_id} and job {job_id}")
        existing_application = Application.get_by_user_and_job(user_id, job_id)
        print(f"Found application: {existing_application}")
        return existing_application is not None

    @staticmethod
    def apply_for_job(user_id, job_id):
        # Check if the job exists and is still active
        job = Job.get_by_id(job_id)
        if not job or not job.is_active:
            return False, "This job is no longer available."

        # Check if the user has already applied
        if UserController.has_applied_for_job(user_id, job_id):
            return False, "You have already applied for this position."

        # Create a new application
        application = Application(user_id=user_id, job_id=job_id)
        success = application.save()

        if success:
            return True, "Your application has been submitted successfully!"
        else:
            return False, "There was an error submitting your application. Please try again."

    @staticmethod
    def revoke_application(user_id, job_id):
        # Check if the job exists and is still active
        job = Job.get_by_id(job_id)
        if not job or not job.is_active:
            return False, "This job is no longer available."

        application = Application.get_by_user_and_job(user_id, job_id)
        if not application:
            return False, "Application not found."

        print(f"application\n{application}")

        # Delete the application
        success = Application.delete_by_application_id(application.application_id)
        if success:
            return True, "Application successfully revoked."
        else:
            return False, "Failed to revoke the application. Please try again."

    @staticmethod
    def delete_by_application_id(application_id):
        return Application.delete_by_application_id(application_id)

    @staticmethod
    def get_recommended_jobs(user):
        """
        Get personalized job recommendations based on user's profile factors:
        - Skills match
        - Location match
        - Certification match
        - Work history relevance

        Returns a list of dictionaries with job details and matched reasons.
        Only includes jobs with at least one matched reason.
        """
        response = DynamoDB.scan(
            'Jobs',
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )

        jobs = [Job(**item) for item in response.get('Items', [])]
        scored_jobs = []

        for job in jobs:
            score = 0
            matched_reasons = {
                'skills': [],
                'location': '',
                'certifications': [],
                'work_history': []
            }

            # Skills matching (highest weight - 40%)
            user_skills = {skill['skill'].lower() for skill in user.skills}
            job_skills = {skill.lower() for skill in job.skills}
            if job_skills and user_skills:
                matched_skills = user_skills.intersection(job_skills)
                skills_match = len(matched_skills) / len(job_skills)
                score += skills_match * 40
                if matched_skills:
                    matched_reasons['skills'] = list(matched_skills)

            # Location matching (30%)
            if user.city and user.country:
                if job.city.lower() == user.city.lower():
                        # and job.country.lower() == user.country.lower():
                    score += 30
                    matched_reasons['location'] = 'City match'

            # Certification matching (20%)
            user_certs = {cert['type'].lower() for cert in user.certifications}
            job_certs = {cert.lower() for cert in job.certifications}
            if job_certs and user_certs:
                matched_certs = user_certs.intersection(job_certs)
                cert_match = len(matched_certs) / len(job_certs)
                score += cert_match * 20
                if matched_certs:
                    matched_reasons['certifications'] = list(matched_certs)

            # Work history relevance (10%)
            user_job_titles = {work['job_title'].lower() for work in user.work_history}
            if job.job_title.lower() in user_job_titles:
                score += 10
                matched_reasons['work_history'].append(job.job_title.lower())

            # Determine if there's at least one matched reason
            has_match = (
                    bool(matched_reasons['skills']) or
                    bool(matched_reasons['location']) or
                    bool(matched_reasons['certifications']) or
                    bool(matched_reasons['work_history'])
            )

            if has_match:
                scored_jobs.append({
                    'job': job,
                    'score': score,
                    'matched_reasons': matched_reasons
                })

        # Sort jobs by score descending and date posted
        scored_jobs.sort(key=lambda x: (x['score'], x['job'].date_posted), reverse=True)

        # Prepare the final list with job and matched reasons
        recommended_jobs = []
        for entry in scored_jobs:
            job = entry['job']
            reasons = entry['matched_reasons']
            recommended_jobs.append({
                'job': job,
                'matched_reasons': reasons,
                'score': entry['score']
            })

        return recommended_jobs

    # New method to get saved jobs for the user
    @staticmethod
    def get_saved_jobs(user_id):
        user = User.get_by_id(user_id)
        if user and user.saved_jobs:
            saved_jobs = [Job.get_by_id(job_id) for job_id in user.saved_jobs]
            return [job for job in saved_jobs if job is not None]
        return []

    # Method to save a job for a user
    @staticmethod
    def save_job(user_id, job_id):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        if job_id in user.saved_jobs:
            return False, "Job already saved."

        user.saved_jobs.append(job_id)
        user.save()
        return True, "Job saved successfully."

    @staticmethod
    def remove_saved_job(user_id, job_id):
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        if job_id not in user.saved_jobs:
            return False, "Job not found in saved jobs."

        user.saved_jobs.remove(job_id)
        user.save()
        return True, "Job removed from saved jobs."

    # New method for retrieving user's job applications
    @staticmethod
    def get_user_applications(user_id):
        """
        Get all applications for a user with associated job details
        """
        applications = Application.get_by_user_id(user_id)

        # For each application, fetch and attach the associated job
        for application in applications:
            try:
                job = Job.get_by_id(application.job_id)
                if job and job.is_active:  # Make sure job exists and is active
                    # Create a simple dictionary with required job info
                    application.job = {
                        'job_title': job.job_title,
                        'company_name': job.company_name,
                        'city': job.city,
                        'country': job.country,
                        'is_active': job.is_active
                    }
                else:
                    application.job = None
            except Exception as e:
                print(f"Error fetching job for application {application.application_id}: {e}")
                application.job = None

        # Sort applications by date_applied (most recent first)
        return sorted(applications, key=lambda x: x.date_applied, reverse=True)

    @staticmethod
    def get_application(user_id, job_id):
        """Get the application details for a specific user and job."""
        return Application.get_by_user_and_job(user_id, job_id)

    # New method for tracking user applications
    @staticmethod
    def get_application_status(user_id):
        return Application.get_by_user_id(user_id)

    # New method for networking events
    @staticmethod
    def get_networking_events():
        # This should ideally get events from the database or an external service
        return [
            {
                'name': 'Tech Networking 2024',
                'date': '2024-12-05',
                'location': 'Online',
                'description': 'Connect with industry professionals in the tech world.',
                'registration_link': 'https://example.com/register'
            },
            {
                'name': 'Women in Tech Summit',
                'date': '2025-01-15',
                'location': 'New York, USA',
                'description': 'A summit focused on opportunities for women in tech.',
                'registration_link': 'https://example.com/register'
            }
        ]

    # New method for getting interview tips
    @staticmethod
    def get_interview_tips():
        return []
