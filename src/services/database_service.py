import boto3
from botocore.exceptions import ClientError
import logging

class DynamoDB:
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

    @classmethod
    def get_item(cls, table_name, key):
        table = cls.dynamodb.Table(table_name)
        try:
            response = table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logging.error(f"Error getting item from {table_name}: {str(e)}")
            return None

    @classmethod
    def put_item(cls, table_name, item):
        table = cls.dynamodb.Table(table_name)
        try:
            table.put_item(Item=item)
            return True
        except ClientError as e:
            logging.error(f"Error putting item into {table_name}: {str(e)}")
            return False

    @classmethod
    def update_item(cls, table_name, key, update_values):
        table = cls.dynamodb.Table(table_name)
        update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_values.keys())
        expression_attribute_values = {f":{k}": v for k, v in update_values.items()}

        try:
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            return True
        except ClientError as e:
            logging.error(f"Error updating item in {table_name}: {str(e)}")
            return False

    @classmethod
    def scan(cls, table_name, FilterExpression=None, ExpressionAttributeValues=None):
        table = cls.dynamodb.Table(table_name)
        try:
            if FilterExpression and ExpressionAttributeValues:
                response = table.scan(
                    FilterExpression=FilterExpression,
                    ExpressionAttributeValues=ExpressionAttributeValues
                )
            else:
                response = table.scan()
            return response
        except ClientError as e:
            logging.error(f"Error scanning table {table_name}: {str(e)}")
            return None

    @classmethod
    def query_by_email(cls, table_name, email):
        table = cls.dynamodb.Table(table_name)
        try:
            response = table.query(
                IndexName='email-index',  # You'll need to create this secondary index
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            return response.get('Items')
        except ClientError as e:
            logging.error(f"Error querying {table_name} by email: {str(e)}")
            return None

    @staticmethod
    def get_all_active_users():
        response = DynamoDB.scan(
            table_name='Users',
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        return response.get('Items', [])

    @staticmethod
    def get_all_active_admins():
        response = DynamoDB.scan(
            table_name='Admins',
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        return response.get('Items', [])

    @staticmethod
    def get_all_users():
        response = DynamoDB.scan(
            table_name='Users'
        )
        return response.get('Items', [])

    @staticmethod
    def get_all_admins():
        response = DynamoDB.scan(
            table_name='Admins'
        )
        return response.get('Items', [])

    @staticmethod
    def query(table_name, index_name, KeyConditionExpression, ExpressionAttributeValues):
        table = DynamoDB.dynamodb.Table(table_name)
        try:
            response = table.query(
                IndexName=index_name,
                KeyConditionExpression=KeyConditionExpression,
                ExpressionAttributeValues=ExpressionAttributeValues
            )
            return response
        except ClientError as e:
            print(e.response['Error']['Message'])
            return {}