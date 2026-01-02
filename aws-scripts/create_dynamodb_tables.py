"""
Create DynamoDB tables locally or on AWS.
Run with: python aws-scripts/create_dynamodb_tables.py [--local]
"""
import boto3
import sys

# Check if --local flag is provided
is_local = '--local' in sys.argv

# DynamoDB setup
if is_local:
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://127.0.0.1:8000',  # Use IP instead of localhost for Windows compatibility
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    print("Creating tables in LOCAL DynamoDB...")
else:
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
    print("Creating tables in AWS DynamoDB...")


def create_users_table():
    """Create users table."""
    table_name = 'myra-users-dev' if is_local else 'myra-users-prod'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        if not is_local:
            table.wait_until_exists()

        print(f"[OK] Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"[WARN] Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_usage_table():
    """Create usage tracking table."""
    table_name = 'myra-usage-dev' if is_local else 'myra-usage-prod'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'date', 'KeyType': 'RANGE'}     # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'date', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        if not is_local:
            table.wait_until_exists()

        print(f"[OK] Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"[WARN] Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_verification_table():
    """Create email verification codes table."""
    table_name = 'myra-verification-dev' if is_local else 'myra-verification-prod'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        if not is_local:
            table.wait_until_exists()

        print(f"[OK] Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"[WARN] Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_organizations_table():
    """Create organizations configuration table."""
    table_name = 'myra-organizations-dev' if is_local else 'myra-organizations-prod'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'org_code', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'org_code', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        if not is_local:
            table.wait_until_exists()

        print(f"[OK] Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"[WARN] Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_research_logs_table():
    """Create research logs metadata table."""
    table_name = 'myra-research-logs-dev' if is_local else 'myra-research-logs-prod'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'log_id', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'log_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'created_at-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        if not is_local:
            table.wait_until_exists()

        print(f"[OK] Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"[WARN] Table {table_name} already exists")
        return dynamodb.Table(table_name)


if __name__ == '__main__':
    print("\nCreating DynamoDB tables...\n")

    users_table = create_users_table()
    usage_table = create_usage_table()
    verification_table = create_verification_table()
    organizations_table = create_organizations_table()
    research_logs_table = create_research_logs_table()

    print("\nDone! Tables created successfully.\n")

    # List tables
    print("Tables:")
    for table_name in dynamodb.meta.client.list_tables()['TableNames']:
        print(f"  - {table_name}")
    print()
