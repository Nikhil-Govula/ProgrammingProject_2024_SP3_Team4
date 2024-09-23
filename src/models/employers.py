class EmployerModel:
    def __init__(self):
        self.table = dynamodb.Table('Employers')

    def get_employer_by_email(self, email):
        response = self.table.get_item(Key={'email': email})
        return response.get('Item')

    def create_employer(self, employer_data):
        self.table.put_item(Item=employer_data)
