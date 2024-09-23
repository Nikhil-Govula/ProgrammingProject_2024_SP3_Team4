import boto3
import os
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

class JobModel:
    def __init__(self):
        self.table = dynamodb.Table('Jobs')

    def create_job(self, job_data):
        """
        Create a new job entry in the DynamoDB table.

        Args:
            job_data (dict): Job details to be stored in the table.
        """
        try:
            self.table.put_item(Item=job_data)
            print(f"Job {job_data['job_id']} created successfully.")
        except Exception as e:
            print(f"Error creating job: {str(e)}")

    def get_jobs_by_employer(self, employer_id):
        """
        Get all jobs posted by a specific employer.

        Args:
            employer_id (str): ID of the employer to filter jobs.

        Returns:
            list: List of jobs posted by the employer.
        """
        try:
            response = self.table.query(
                IndexName='EmployerIndex',  # Ensure this index exists in your table
                KeyConditionExpression=Key('employer_id').eq(employer_id)
            )
            jobs = response.get('Items', [])
            if not jobs:
                print(f"No jobs found for employer_id: {employer_id}")
            return jobs
        except Exception as e:
            print(f"Error fetching jobs: {str(e)}")
            return []
