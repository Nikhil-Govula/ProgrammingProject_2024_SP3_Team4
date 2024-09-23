class JobModel:
    def __init__(self):
        self.table = dynamodb.Table('Jobs')

    def create_job(self, job_data):
        self.table.put_item(Item=job_data)

    def get_jobs_by_employer(self, employer_id):
        response = self.table.query(
            IndexName='EmployerIndex',
            KeyConditionExpression=Key('employer_id').eq(employer_id)
        )
        return response.get('Items')
