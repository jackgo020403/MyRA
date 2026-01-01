"""Quick test to see if DynamoDB connection works."""
import boto3

print("Testing DynamoDB connection...")

try:
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://127.0.0.1:8000',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    print("Connected! Listing tables...")
    tables = dynamodb.meta.client.list_tables()
    print(f"Tables: {tables}")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
