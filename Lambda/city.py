import boto3
import csv
import os
import json
from functools import lru_cache

s3_client = boto3.client('s3')
CSV_BUCKET = os.environ['CSV_BUCKET']
CSV_KEY = os.environ['CSV_KEY']

# Global variable to cache city data
city_data = []


def load_city_data():
    global city_data
    if not city_data:
        try:
            print("Loading city data from S3.")
            response = s3_client.get_object(Bucket=CSV_BUCKET, Key=CSV_KEY)
            lines = response['Body'].read().decode('utf-8').splitlines()
            reader = csv.DictReader(lines)
            # Extract city and country names and store in a list of dictionaries
            city_data = [{'city': row['city'].lower(), 'country': row['country'].lower(),
                          'original_city': row['city'], 'original_country': row['country']}
                         for row in reader if row.get('city') and row.get('country')]
            print(f"Loaded {len(city_data)} cities.")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            city_data = []


@lru_cache(maxsize=1024)
def get_suggestions(query):
    return [
               {'city': item['original_city'], 'country': item['original_country']}
               for item in city_data
               if query in item['city'] or query in item['country']
           ][:10]


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    load_city_data()

    # Extract 'query' parameter from the event
    query = event.get('queryStringParameters', {}).get('query', '').strip().lower()
    print(f"Query: {query}")

    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing query parameter.'})
        }

    suggestions = get_suggestions(query)
    print(f"Suggestions: {suggestions}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # Adjust as needed for CORS
        },
        'body': json.dumps({'suggestions': suggestions})
    }