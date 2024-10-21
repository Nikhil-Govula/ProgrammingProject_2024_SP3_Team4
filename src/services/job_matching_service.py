# src/services/job_matching_service.py

from .database_service import DynamoDB
from ..models.user_model import User
from ..models.job_model import Job

class JobMatchingService:
    @staticmethod
    def match_jobs_to_user(user):
        user_skills = set(user.skills)
        user_certifications = set(user.certifications)
        user_location = user.location.lower()

        jobs = Job.get_all_jobs()
        matched_jobs = []

        for job in jobs:
            job_skills = set(job.skills)
            job_certifications = set(job.certifications)
            job_location = job.location.lower()

            # Simple matching criteria:
            # 1. User has all required skills
            # 2. User has all required certifications
            # 3. User's location matches job location or is within a certain radius (simplified here)

            if not job_skills.issubset(user_skills):
                continue

            if not job_certifications.issubset(user_certifications):
                continue

            if user_location != job_location:
                continue

            matched_jobs.append(job)

        return matched_jobs

    @staticmethod
    def match_users_to_job(job):
        job_skills = set(job.skills)
        job_certifications = set(job.certifications)
        job_location = job.location.lower()

        users = User.get_all_users()
        matched_users = []

        for user in users:
            user_skills = set(user.skills)
            user_certifications = set(user.certifications)
            user_location = user.location.lower()

            if not job_skills.issubset(user_skills):
                continue

            if not job_certifications.issubset(user_certifications):
                continue

            if user_location != job_location:
                continue

            matched_users.append(user)

        return matched_users
