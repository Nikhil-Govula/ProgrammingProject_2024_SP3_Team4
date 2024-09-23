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