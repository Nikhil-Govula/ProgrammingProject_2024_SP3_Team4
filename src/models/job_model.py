# src/models/job_model.py

from decimal import Decimal

from ..models.application_model import Application
from ..services.database_service import DynamoDB
import uuid
import datetime

class Job:
    def __init__(self, job_id, employer_id, job_title, description, requirements, salary, city, country, certifications, skills, work_history, company_name, date_posted=None, is_active=True):
        self.job_id = job_id or str(uuid.uuid4())
        self.employer_id = employer_id
        self.job_title = job_title
        self.description = description
        self.requirements = requirements
        try:
            self.salary = Decimal(salary)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid salary value: {salary}") from e
        self.city = city
        self.country = country
        self.certifications = certifications or []
        self.skills = skills or []
        self.work_history = work_history or []  # Initialize as a list
        self.company_name = company_name
        self.date_posted = date_posted or datetime.datetime.utcnow().isoformat()
        self.is_active = is_active

    def save_with_response(self):
        try:
            result = DynamoDB.put_item('Jobs', self.to_dict())
            if result:
                return True, "Job saved successfully."
            else:
                return False, "Failed to save job."
        except Exception as e:
            print(f"Error saving job: {e}")
            return False, "An error occurred while saving the job."

    @staticmethod
    def get_by_id(job_id):
        item = DynamoDB.get_item('Jobs', {'job_id': job_id})
        if item:
            return Job(**item)
        return None

    @staticmethod
    def get_all_jobs():
        response = DynamoDB.scan('Jobs', FilterExpression='is_active = :active', ExpressionAttributeValues={':active': True})
        return [Job(**item) for item in response.get('Items', [])]

    @staticmethod
    def get_jobs_by_employer(employer_id):
        response = DynamoDB.scan('Jobs', FilterExpression='employer_id = :eid AND is_active = :active',
                                 ExpressionAttributeValues={':eid': employer_id, ':active': True})
        jobs = [Job(**item) for item in response.get('Items', [])]
        return sorted(jobs, key=lambda x: x.date_posted, reverse=True)

    def delete(self):
        self.is_active = False
        DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'is_active': False})

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'employer_id': self.employer_id,
            'job_title': self.job_title,
            'description': self.description,
            'requirements': self.requirements,
            'salary': self.salary,
            'city': self.city,
            'country': self.country,
            'certifications': self.certifications,
            'skills': self.skills,
            'work_history': self.work_history,  # Store as a list of dicts
            'company_name': self.company_name,
            'date_posted': self.date_posted,
            'is_active': self.is_active
        }

    def add_skill(self, skill):
        if skill in self.skills:
            print(f"Skill '{skill}' is already added.")  # Debug log
            return False, f"The skill '{skill}' is already added to this job."

        print(f"Adding skill '{skill}'")  # Debug log
        self.skills.append(skill)
        success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'skills': self.skills})

        if success:
            print(f"Skill '{skill}' added successfully.")  # Debug log
        else:
            print(f"Failed to add skill '{skill}'")  # Debug log

        return success, f"Skill '{skill}' added successfully."

    def remove_skill(self, skill):
        if skill in self.skills:
            self.skills.remove(skill)
            success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'skills': self.skills})
            return success, "Skill removed successfully"
        return False, "Skill not found"

    def add_certification(self, certification):
        if certification not in self.certifications:
            self.certifications.append(certification)
            success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'certifications': self.certifications})
            return success, certification
        return False, "Certification already exists"

    def remove_certification(self, certification):
        if certification in self.certifications:
            self.certifications.remove(certification)
            success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'certifications': self.certifications})
            return success, "Certification removed successfully"
        return False, "Certification not found"

    def add_work_history_entry(self, occupation, duration):
        # Check for duplicate entry
        for entry in self.work_history:
            if entry['occupation'] == occupation and entry['duration'] == duration:
                print(f"Work history entry '{occupation} - {duration} months' already exists.")
                return False, f"The work history entry '{occupation} - {duration} months' is already added to this job."

        print(f"Adding work history entry: {occupation} - {duration} months")  # Debug log
        self.work_history.append({'occupation': occupation, 'duration': duration})
        success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'work_history': self.work_history})

        if success:
            print(f"Work history entry '{occupation} - {duration} months' added successfully.")  # Debug log
        else:
            print(f"Failed to add work history entry '{occupation} - {duration} months'")  # Debug log

        return success, f"Work history entry '{occupation} - {duration} months' added successfully."

    def remove_work_history_entry(self, occupation, duration):
        entry_to_remove = None
        for entry in self.work_history:
            if entry['occupation'] == occupation and entry['duration'] == duration:
                entry_to_remove = entry
                break

        if entry_to_remove:
            self.work_history.remove(entry_to_remove)
            success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, {'work_history': self.work_history})
            if success:
                return True, f"Work history entry '{occupation} - {duration} months' removed successfully."
            else:
                return False, f"Failed to remove work history entry '{occupation} - {duration} months'."
        return False, "Work history entry not found."

    def update_fields(self, fields):
        try:
            success = DynamoDB.update_item('Jobs', {'job_id': self.job_id}, fields)
            if success:
                for key, value in fields.items():
                    setattr(self, key, value)
                return True, "Job updated successfully."
            else:
                return False, "Failed to update job."
        except Exception as e:
            print(f"Error updating Job: {e}")
            return False, str(e)

    @staticmethod
    def get_all_active_jobs():
        """
        Retrieve all active jobs from the database.
        """
        response = DynamoDB.scan(
            'Jobs',
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        jobs = [Job(**item) for item in response.get('Items', [])]
        # Sort jobs by date_posted descending
        sorted_jobs = sorted(jobs, key=lambda x: x.date_posted, reverse=True)
        return sorted_jobs

    @staticmethod
    def get_recommended_jobs(user):
        """
        Get personalized job recommendations based on user's profile factors:
        - Skills match
        - Location match
        - Certification match
        - Work history relevance

        Returns jobs sorted by match score
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

            # Skills matching (highest weight - 40%)
            user_skills = {skill['skill'].lower() for skill in user.skills}
            job_skills = {skill.lower() for skill in job.skills}
            if job_skills and user_skills:  # Avoid division by zero
                skills_match = len(user_skills.intersection(job_skills)) / len(job_skills)
                score += skills_match * 40

            # Location matching (30%)
            if user.city and user.country:
                if job.city.lower() == user.city.lower() and job.country.lower() == user.country.lower():
                    score += 30
                elif job.country.lower() == user.country.lower():
                    score += 15

            # Certification matching (20%)
            user_certs = {cert['type'].lower() for cert in user.certifications}
            job_certs = {cert.lower() for cert in job.certifications}
            if job_certs and user_certs:
                cert_match = len(user_certs.intersection(job_certs)) / len(job_certs)
                score += cert_match * 20

            # Work history relevance (10%)
            user_job_titles = {work['job_title'].lower() for work in user.work_history}
            if job.job_title.lower() in user_job_titles:
                score += 10

            scored_jobs.append((job, score))

        # Sort by score descending and date posted
        scored_jobs.sort(key=lambda x: (x[1], x[0].date_posted), reverse=True)

        # Return only the jobs, not the scores
        return [job for job, score in scored_jobs]

    @staticmethod
    def get_by_id(job_id):
        """
        Retrieve a job by its ID.
        """
        item = DynamoDB.get_item('Jobs', {'job_id': job_id})
        if item:
            return Job(**item)
        return None

    def get_applications(self):
        """Get all applications for this job with user details"""
        from ..models import User  # Import here to avoid circular imports

        response = DynamoDB.scan(
            'Applications',
            FilterExpression='job_id = :jid',
            ExpressionAttributeValues={':jid': self.job_id}
        )

        applications = []
        for app_data in response.get('Items', []):
            # Convert the raw application data to an Application object
            application = Application(**app_data)

            # Get the user details
            user = User.get_by_id(application.user_id)
            if user:
                application_dict = {
                    'application': {
                        'application_id': application.application_id,
                        'status': application.status,
                        'date_applied': application.date_applied
                    },
                    'user': {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'skills': user.skills,
                        'work_history': user.work_history,
                        'profile_picture_url': user.profile_picture_url
                    }
                }
                applications.append(application_dict)

        return applications