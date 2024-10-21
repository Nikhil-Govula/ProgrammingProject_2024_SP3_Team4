# src/models/job_model.py

from decimal import Decimal
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
        self.work_history = work_history
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
            'work_history': self.work_history,
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