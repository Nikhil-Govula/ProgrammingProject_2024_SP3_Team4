from flask import g

from ..models.employer_model import Employer
from ..controllers.user_controller import UserController  # For password validation
from ..services.email_service import send_reset_email
from ..models.job_model import Job
import datetime
import bcrypt
from decimal import Decimal  # Import Decimal

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

        # Validate password strength
        is_valid, message = UserController.validate_password(password)
        if not is_valid:
            return False, message

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_employer = Employer(
            employer_id=None,  # This will be generated automatically
            company_name=company_name,
            email=email,
            password=hashed_password,
            contact_person=contact_person,
            phone_number=phone_number
        )
        success = new_employer.save()
        if success:
            return True, "Employer registered successfully."
        else:
            return False, "Failed to register employer."

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

    @staticmethod
    def create_job(employer_id, job_title, description, requirements, salary, city, country, certifications, skills,
                   work_history, company_name):
        try:
            print(f"Salary before conversion: {salary}")
            salary_decimal = Decimal(salary)
            print(f"Salary after conversion: {salary_decimal}")

        except (ValueError, TypeError) as e:
            return False, f"Invalid salary value: {salary}"

        new_job = Job(
            job_id=None,
            employer_id=employer_id,
            job_title=job_title,
            description=description,
            requirements=requirements,
            salary=salary_decimal,  # Pass Decimal
            city=city,  # New parameter
            country=country,  # New parameter
            certifications=certifications,
            skills=skills,
            work_history=work_history,
            company_name=company_name
        )
        success, message = new_job.save_with_response()
        if success:
            # Optionally, notify users or perform other actions
            # send_job_posted_email(new_job)  # Implement this if you want to notify users
            return True, "Job posted successfully."
        else:
            return False, "Failed to post job."

    @staticmethod
    def update_job(job_id, fields):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        # Handle splitting of 'city' into 'city' and 'country'
        if 'city' in fields:
            city_input = fields.pop('city')
            try:
                city, country = map(str.strip, city_input.split(',', 1))
                fields['city'] = city
                fields['country'] = country
            except ValueError:
                return False, "Invalid city format. Please use 'City, Country'."

        try:
            success, message = job.update_fields(fields)
            return success, message
        except Exception as e:
            print(f"Error updating job: {e}")
            return False, "An unexpected error occurred while updating the job."

    @staticmethod
    def delete_job(job_id):
        job = Job.get_by_id(job_id)
        if job:
            # Ensure the employer has permission to delete this job
            if job.employer_id != g.user.employer_id:
                return False, "You do not have permission to delete this job."
            job.delete()
            return True, "Job deleted successfully."
        else:
            return False, "Job not found."

    @staticmethod
    def list_employer_jobs(employer_id):
        jobs = Job.get_jobs_by_employer(employer_id)
        # Sort jobs by date_posted descending
        sorted_jobs = sorted(jobs, key=lambda x: x.date_posted, reverse=True)
        return sorted_jobs

    @staticmethod
    def add_job_skill(job_id, skill):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, message = job.add_skill(skill)
        return success, message

    @staticmethod
    def remove_job_skill(job_id, skill):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, message = job.remove_skill(skill)
        return success, message

    @staticmethod
    def add_job_certification(job_id, certification):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, result = job.add_certification(certification)
        return success, result

    @staticmethod
    def remove_job_certification(job_id, certification):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, message = job.remove_certification(certification)
        return success, message

    # **New Methods for Work History**

    @staticmethod
    def add_job_work_history(job_id, occupation, duration):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, message = job.add_work_history_entry(occupation, duration)
        return success, message

    @staticmethod
    def remove_job_work_history(job_id, occupation, duration):
        job = Job.get_by_id(job_id)
        if not job:
            return False, "Job not found."

        if job.employer_id != g.user.employer_id:
            return False, "You do not have permission to edit this job."

        success, message = job.remove_work_history_entry(occupation, duration)
        return success, message