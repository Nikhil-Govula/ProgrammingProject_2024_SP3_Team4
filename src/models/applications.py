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

class ApplicationModel:
    def __init__(self):
        self.table = dynamodb.Table('Applications')

    def create_application(self, application_data):
        """
        Create a new application entry in the DynamoDB table.

        Args:
            application_data (dict): Application details to be stored in the table.
        """
        try:
            self.table.put_item(Item=application_data)
            print(f"Application {application_data['application_id']} created successfully.")
        except Exception as e:
            print(f"Error creating application: {str(e)}")

    def get_applications_by_job(self, job_id):
        """
        Get all applications submitted for a specific job.

        Args:
            job_id (str): ID of the job to filter applications.

        Returns:
            list: List of applications submitted for the job.
        """
        try:
            response = self.table.query(
                IndexName='JobIndex',  # Ensure this index exists in your table
                KeyConditionExpression=Key('job_id').eq(job_id)
            )
            applications = response.get('Items', [])
            if not applications:
                print(f"No applications found for job_id: {job_id}")
            return applications
        except Exception as e:
            print(f"Error fetching applications: {str(e)}")
            return []

    def update_application_status(self, application_id, status):
        """
        Update the status of an application.

        Args:
            application_id (str): ID of the application to be updated.
            status (str): New status to set for the application.
        """
        try:
            self.table.update_item(
                Key={'application_id': application_id},
                UpdateExpression="set application_status = :s",
                ExpressionAttributeValues={':s': status}
            )
            print(f"Application {application_id} status updated to {status}.")
        except Exception as e:
            print(f"Error updating application status: {str(e)}")
