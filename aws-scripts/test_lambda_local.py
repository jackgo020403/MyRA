"""
Test Lambda function running locally in Docker.

Prerequisites:
1. Docker Compose running: docker-compose up -d
2. DynamoDB tables created: python aws-scripts/create_dynamodb_tables.py --local

Run with: python aws-scripts/test_lambda_local.py
"""
import requests
import json

LAMBDA_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"


def test_signup():
    """Test user signup."""
    print("\n🧪 Testing signup...")

    event = {
        "body": json.dumps({
            "action": "signup",
            "email": "test@example.com",
            "password": "secure123"
        })
    }

    response = requests.post(LAMBDA_URL, json=event)
    result = response.json()

    print(f"Status: {result['statusCode']}")
    print(f"Response: {json.dumps(json.loads(result['body']), indent=2)}")

    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        return body.get('token'), body.get('user_id')

    return None, None


def test_login():
    """Test user login."""
    print("\n🧪 Testing login...")

    event = {
        "body": json.dumps({
            "action": "login",
            "email": "test@example.com",
            "password": "secure123"
        })
    }

    response = requests.post(LAMBDA_URL, json=event)
    result = response.json()

    print(f"Status: {result['statusCode']}")
    print(f"Response: {json.dumps(json.loads(result['body']), indent=2)}")

    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        return body.get('token'), body.get('user_id')

    return None, None


def test_check_usage(user_id):
    """Test usage checking."""
    print(f"\n🧪 Testing check usage for user: {user_id}...")

    event = {
        "body": json.dumps({
            "action": "check_usage",
            "user_id": user_id
        })
    }

    response = requests.post(LAMBDA_URL, json=event)
    result = response.json()

    print(f"Status: {result['statusCode']}")
    print(f"Response: {json.dumps(json.loads(result['body']), indent=2)}")


def test_increment_usage(user_id):
    """Test usage increment."""
    print(f"\n🧪 Testing increment usage for user: {user_id}...")

    event = {
        "body": json.dumps({
            "action": "increment_usage",
            "user_id": user_id
        })
    }

    response = requests.post(LAMBDA_URL, json=event)
    result = response.json()

    print(f"Status: {result['statusCode']}")
    print(f"Response: {json.dumps(json.loads(result['body']), indent=2)}")


if __name__ == '__main__':
    print("🚀 Testing Lambda function locally...\n")
    print("Make sure Docker Compose is running: docker-compose up -d\n")

    # Test signup
    token, user_id = test_signup()

    if token and user_id:
        # Test login
        test_login()

        # Test usage checking
        test_check_usage(user_id)

        # Test usage increment
        test_increment_usage(user_id)
        test_increment_usage(user_id)

        # Check usage again
        test_check_usage(user_id)

    print("\n✨ Tests complete!\n")
