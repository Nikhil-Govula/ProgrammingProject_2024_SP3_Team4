class ApplicationModel:
    def __init__(self):
        self.table = dynamodb.Table('Applications')

    def create_application(self, application_data):
        self.table.put_item(Item=application_data)

    def get_applications_by_job(self, job_id):
        response = self.table.query(
            IndexName='JobIndex',
            KeyConditionExpression=Key('job_id').eq(job_id)
        )
        return response.get('Items')

    def update_application_status(self, application_id, status):
        self.table.update_item(
            Key={'application_id': application_id},
            UpdateExpression="set application_status = :s",
            ExpressionAttributeValues={':s': status}
        )
