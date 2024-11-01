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
    def update_item(cls, table_name, key, update_values, attribute_names=None):
        table = cls.dynamodb.Table(table_name)

        # Handle reserved keywords if attribute_names is provided
        if attribute_names:
            # Use the attribute names mapping for the update expression
            update_expression = "SET " + ", ".join(f"{k} = :{k.replace('#', '')}" for k in update_values.keys())
            expression_attribute_values = {f":{k.replace('#', '')}": v for k, v in update_values.items()}

            try:
                table.update_item(
                    Key=key,
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames=attribute_names
                )
                return True
            except ClientError as e:
                logging.error(f"Error updating item in {table_name}: {str(e)}")
                return False
        else:
            # Original behavior for backward compatibility
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
    def scan(cls, table_name, FilterExpression=None, ExpressionAttributeValues=None, ExpressionAttributeNames=None):
        table = cls.dynamodb.Table(table_name)
        try:
            scan_kwargs = {}
            if FilterExpression:
                scan_kwargs['FilterExpression'] = FilterExpression
            if ExpressionAttributeValues:
                scan_kwargs['ExpressionAttributeValues'] = ExpressionAttributeValues
            if ExpressionAttributeNames:
                scan_kwargs['ExpressionAttributeNames'] = ExpressionAttributeNames

            response = table.scan(**scan_kwargs)
            return response
        except ClientError as e:
            print(f"Error scanning table {table_name}: {str(e)}")
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

    @classmethod
    def delete_item(cls, table_name, key):
        table = cls.dynamodb.Table(table_name)
        try:
            table.delete_item(Key=key)
            print(f"delete action performed on {table_name}")
            return True
        except ClientError as e:
            logging.error(f"Error deleting item from {table_name}: {str(e)}")
            return False
