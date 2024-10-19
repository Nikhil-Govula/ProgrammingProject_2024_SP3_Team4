# src/models/job_model.py

from ..services.database_service import DynamoDB
import uuid
import datetime

class Job:
    def __init__(self, job_id, employer_id, job_title, description, requirements, salary, location, certifications, skills, work_history, company_name, date_posted=None, is_active=True):
        self.job_id = job_id or str(uuid.uuid4())
        self.employer_id = employer_id
        self.job_title = job_title
        self.description = description
        self.requirements = requirements  # This can be a list or a string
        self.salary = salary
        self.location = location
        self.certifications = certifications  # List of required certifications
        self.skills = skills  # List of required skills
        self.work_history = work_history  # Required work history
        self.company_name = company_name
        self.date_posted = date_posted or datetime.datetime.utcnow().isoformat()
        self.is_active = is_active

    def save(self):
        return DynamoDB.put_item('Jobs', self.to_dict())

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
        # Sort jobs by date_posted descending
        sorted_jobs = sorted(jobs, key=lambda x: x.date_posted, reverse=True)
        return sorted_jobs

    def update_fields(self, fields):
        try:
            for key, value in fields.items():
                if hasattr(self, key) and key not in ['job_id', 'employer_id', 'date_posted']:
                    setattr(self, key, value)
            DynamoDB.update_item('Jobs', {'job_id': self.job_id},
                                 fields)
            return True, "Job updated successfully."
        except Exception as e:
            print(f"Error updating Job: {e}")
            return False, str(e)

    def delete(self):
        # Soft delete by setting is_active to False
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
            'location': self.location,
            'certifications': self.certifications,
            'skills': self.skills,
            'work_history': self.work_history,
            'company_name': self.company_name,
            'date_posted': self.date_posted,
            'is_active': self.is_active
        }
