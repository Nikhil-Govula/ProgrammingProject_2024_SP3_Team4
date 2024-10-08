import json
import boto3
import csv
import os
from functools import lru_cache

s3_client = boto3.client('s3')
CSV_BUCKET = os.environ['CSV_BUCKET']
CSV_KEY = os.environ['CSV_KEY']

# Global variable to cache skill data
skill_data = []


def load_skill_data():
    global skill_data
    if not skill_data:
        try:
            print("Loading skill data from S3.")
            response = s3_client.get_object(Bucket=CSV_BUCKET, Key=CSV_KEY)
            content = response['Body'].read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(content)
            skill_data = [row['Skill'].lower() for row in reader if row.get('Skill')]
            print(f"Loaded {len(skill_data)} skills.")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            skill_data = []


@lru_cache(maxsize=1024)
def get_suggestions(query):
    return [ski for ski in skill_data if query in ski][:10]


def lambda_handler(event, context):
    query = event.get('queryStringParameters', {}).get('query', '').strip().lower()

    if not query:
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'suggestions': []})
        }

    load_skill_data()

    try:
        suggestions = get_suggestions(query)

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'suggestions': suggestions})
        }

    except Exception as e:
        print(f"Error fetching skills: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }