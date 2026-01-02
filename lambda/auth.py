"""
AWS Lambda function for organization-based user authentication.
Handles: signup with email verification, login, usage tracking per organization
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import jwt
import bcrypt
import secrets
from typing import Dict, Any
from config import (
    ORGANIZATIONS,
    validate_email_domain,
    get_organization_by_email,
    get_api_keys,
    get_daily_limit
)


# Helper function to convert DynamoDB Decimal to int/float for JSON serialization
def decimal_to_number(obj):
    """Convert Decimal objects to int or float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(item) for item in obj]
    return obj

# DynamoDB setup
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'),  # None in prod, http://dynamodb-local:8000 in dev
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

USERS_TABLE = os.environ.get('DYNAMODB_TABLE_USERS', 'myra-users')
USAGE_TABLE = os.environ.get('DYNAMODB_TABLE_USAGE', 'myra-usage')
ORGS_TABLE = os.environ.get('DYNAMODB_TABLE_ORGS', 'myra-organizations')
VERIFICATION_TABLE = os.environ.get('DYNAMODB_TABLE_VERIFICATION', 'myra-verification')
RESEARCH_LOGS_TABLE = os.environ.get('DYNAMODB_TABLE_RESEARCH_LOGS', 'myra-research-logs')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
S3_BUCKET = os.environ.get('S3_RESEARCH_LOGS_BUCKET', 'myra-research-logs')

users_table = dynamodb.Table(USERS_TABLE)
usage_table = dynamodb.Table(USAGE_TABLE)
orgs_table = dynamodb.Table(ORGS_TABLE)
verification_table = dynamodb.Table(VERIFICATION_TABLE)
research_logs_table = dynamodb.Table(RESEARCH_LOGS_TABLE)

# S3 client for storing research files
s3_client = boto3.client('s3', region_name='ap-northeast-2')


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(user_id: str, email: str, organization: str) -> str:
    """Generate JWT token with organization info."""
    payload = {
        'user_id': user_id,
        'email': email,
        'organization': organization,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def generate_verification_code() -> str:
    """Generate 6-digit verification code."""
    return f"{secrets.randbelow(1000000):06d}"


def send_verification_email(email: str, code: str, organization: str) -> bool:
    """Send verification email with code using AWS SES."""
    org_name = ORGANIZATIONS[organization]["name"]

    # Get sender email from environment or use default
    sender_email = os.environ.get('SES_SENDER_EMAIL', 'noreply@myra-research.com')

    try:
        # Use SES in us-east-1 (SES is only available in certain regions)
        ses = boto3.client('ses', region_name='us-east-1')

        subject = f"Verify your MyRA account - {org_name}"

        body_text = f"""
Welcome to MyRA Research Assistant!

Your verification code is: {code}

This code will expire in 10 minutes.

Organization: {org_name}

If you didn't request this verification, please ignore this email.

---
MyRA Research Assistant
"""

        body_html = f"""
<html>
<head></head>
<body>
  <h2>Welcome to MyRA Research Assistant!</h2>
  <p>Your verification code is:</p>
  <h1 style="color: #1976D2; font-size: 32px; letter-spacing: 5px;">{code}</h1>
  <p>This code will expire in 10 minutes.</p>
  <p><strong>Organization:</strong> {org_name}</p>
  <hr>
  <p style="color: #666; font-size: 12px;">
    If you didn't request this verification, please ignore this email.
  </p>
</body>
</html>
"""

        response = ses.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            }
        )

        print(f"✓ Verification email sent to {email} (MessageId: {response['MessageId']})")
        return True

    except Exception as e:
        # Log error but don't fail the signup - print code to logs as fallback
        print(f"✗ Failed to send email to {email}: {str(e)}")
        print(f"FALLBACK - Verification code for {email}: {code}")
        return False


def signup(email: str, password: str, organization: str, name: str = "") -> Dict[str, Any]:
    """
    Create new user account with organization validation.

    Args:
        email: User's email address
        password: User's password (will be hashed)
        organization: Organization code (e.g., "SNU_student", "McKinsey")
        name: User's full name (optional)

    Returns:
        Response with status and verification code info
    """
    try:
        # Validate organization exists
        if organization not in ORGANIZATIONS:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid organization',
                    'available_organizations': list(ORGANIZATIONS.keys())
                })
            }

        # Validate email domain matches organization
        if not validate_email_domain(email, organization):
            allowed_domains = ORGANIZATIONS[organization]["email_domains"]
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Email must end with one of: {", ".join(allowed_domains)}',
                    'organization': organization
                })
            }

        # Check if user already exists
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email already registered'})
            }

        # Create user (unverified)
        user_id = f"user_{organization}_{int(datetime.utcnow().timestamp() * 1000)}"
        hashed_pw = hash_password(password)

        # Generate verification code
        verification_code = generate_verification_code()
        verification_expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

        # Store verification code
        verification_table.put_item(Item={
            'email': email,
            'code': verification_code,
            'expires_at': verification_expires,
            'created_at': datetime.utcnow().isoformat()
        })

        # Create user (unverified status)
        users_table.put_item(Item={
            'email': email,
            'user_id': user_id,
            'password_hash': hashed_pw,
            'organization': organization,
            'name': name,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat(),
            'daily_limit': get_daily_limit(organization),
            'status': 'pending_verification'
        })

        # Initialize usage tracking
        usage_table.put_item(Item={
            'user_id': user_id,
            'date': datetime.utcnow().date().isoformat(),
            'searches_used': 0,
            'organization': organization
        })

        # Send verification email
        send_verification_email(email, verification_code, organization)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Verification code sent to your email',
                'user_id': user_id,
                'email': email,
                'organization': organization,
                'requires_verification': True
            })
        }
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def verify_email(email: str, code: str) -> Dict[str, Any]:
    """
    Verify user's email with verification code.

    Args:
        email: User's email address
        code: 6-digit verification code

    Returns:
        Response with JWT token if successful
    """
    try:
        # Get verification code
        response = verification_table.get_item(Key={'email': email})

        if 'Item' not in response:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No verification code found. Please sign up again.'})
            }

        verification = response['Item']

        # Check if code matches
        if verification['code'] != code:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid verification code'})
            }

        # Check if expired
        expires_at = datetime.fromisoformat(verification['expires_at'])
        if datetime.utcnow() > expires_at:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Verification code expired. Please sign up again.'})
            }

        # Get user
        user_response = users_table.get_item(Key={'email': email})
        if 'Item' not in user_response:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'User not found'})
            }

        user = user_response['Item']

        # Update user as verified
        users_table.update_item(
            Key={'email': email},
            UpdateExpression='SET email_verified = :verified, #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':verified': True,
                ':status': 'active'
            }
        )

        # Delete verification code
        verification_table.delete_item(Key={'email': email})

        # Generate token
        token = generate_token(user['user_id'], email, user['organization'])

        response_data = {
            'message': 'Email verified successfully',
            'token': token,
            'user_id': user['user_id'],
            'email': email,
            'organization': user['organization'],
            'daily_limit': user.get('daily_limit', 10)
        }

        return {
            'statusCode': 200,
            'body': json.dumps(decimal_to_number(response_data))
        }
    except Exception as e:
        print(f"Verification error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def login(email: str, password: str) -> Dict[str, Any]:
    """
    Login existing user.

    Args:
        email: User's email address
        password: User's password

    Returns:
        Response with JWT token if successful
    """
    try:
        response = users_table.get_item(Key={'email': email})

        if 'Item' not in response:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid credentials'})
            }

        user = response['Item']

        # Check if email is verified
        if not user.get('email_verified', False):
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Email not verified. Please check your email for verification code.',
                    'requires_verification': True
                })
            }

        # Verify password
        if not verify_password(password, user['password_hash']):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid credentials'})
            }

        # Generate token
        token = generate_token(user['user_id'], email, user['organization'])

        response_data = {
            'message': 'Login successful',
            'token': token,
            'user_id': user['user_id'],
            'email': email,
            'organization': user['organization'],
            'name': user.get('name', ''),
            'daily_limit': user.get('daily_limit', 10)
        }

        return {
            'statusCode': 200,
            'body': json.dumps(decimal_to_number(response_data))
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def check_usage(user_id: str) -> Dict[str, Any]:
    """Check if user has remaining searches for today."""
    try:
        today = datetime.utcnow().date().isoformat()

        # Get usage
        response = usage_table.get_item(Key={
            'user_id': user_id,
            'date': today
        })

        # Get user's organization and daily limit
        # Extract email from user_id pattern or query by GSI
        # For now, we'll need to pass organization or query user
        # Simplified: assume we get it from token

        if 'Item' in response:
            usage = response['Item']
            searches_used = usage.get('searches_used', 0)
            organization = usage.get('organization', 'SNU_student')
        else:
            searches_used = 0
            organization = 'SNU_student'  # Default

        daily_limit = get_daily_limit(organization)
        remaining = daily_limit - searches_used

        response_data = {
            'searches_used': searches_used,
            'daily_limit': daily_limit,
            'remaining': remaining,
            'can_search': remaining > 0,
            'organization': organization
        }

        return {
            'statusCode': 200,
            'body': json.dumps(decimal_to_number(response_data))
        }
    except Exception as e:
        print(f"Check usage error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def increment_usage(user_id: str, organization: str) -> Dict[str, Any]:
    """Increment user's search count for today."""
    try:
        today = datetime.utcnow().date().isoformat()

        # Update or create usage record
        usage_table.update_item(
            Key={
                'user_id': user_id,
                'date': today
            },
            UpdateExpression='SET searches_used = if_not_exists(searches_used, :zero) + :inc, organization = :org',
            ExpressionAttributeValues={
                ':inc': 1,
                ':zero': 0,
                ':org': organization
            }
        )

        return check_usage(user_id)
    except Exception as e:
        print(f"Increment usage error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_user_api_keys(user_id: str) -> Dict[str, Any]:
    """
    Get API keys for user's organization.
    NEVER expose keys to client - this is for server-side use only.
    """
    try:
        # Get user to find organization
        # This is a simplified approach - in production use GSI
        # For now, we'll pass organization in the request

        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'API keys are server-side only'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def resend_verification(email: str) -> Dict[str, Any]:
    """Resend verification code."""
    try:
        # Get user
        response = users_table.get_item(Key={'email': email})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        user = response['Item']

        if user.get('email_verified', False):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email already verified'})
            }

        # Generate new code
        verification_code = generate_verification_code()
        verification_expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

        # Update verification code
        verification_table.put_item(Item={
            'email': email,
            'code': verification_code,
            'expires_at': verification_expires,
            'created_at': datetime.utcnow().isoformat()
        })

        # Send email
        send_verification_email(email, verification_code, user['organization'])

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Verification code sent'})
        }
    except Exception as e:
        print(f"Resend verification error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def save_research_log(user_id: str, research_title: str, research_question: str, file_data: bytes, file_name: str) -> Dict[str, Any]:
    """
    Save research log to DynamoDB and S3.

    Args:
        user_id: User's ID
        research_title: Title of the research
        research_question: Original research question
        file_data: Excel file bytes
        file_name: Original filename

    Returns:
        Response with log_id and metadata
    """
    try:
        import base64

        # Generate unique log ID
        log_id = f"log_{int(datetime.utcnow().timestamp() * 1000)}"
        created_at = datetime.utcnow().isoformat()

        # S3 key pattern: {user_id}/{log_id}/{filename}
        s3_key = f"{user_id}/{log_id}/{file_name}"

        # Decode base64 file data if needed
        if isinstance(file_data, str):
            file_bytes = base64.b64decode(file_data)
        else:
            file_bytes = file_data

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            Metadata={
                'user_id': user_id,
                'log_id': log_id,
                'research_title': research_title,
                'created_at': created_at
            }
        )

        # Save metadata to DynamoDB
        research_logs_table.put_item(Item={
            'user_id': user_id,
            'log_id': log_id,
            'research_title': research_title,
            'research_question': research_question,
            'file_name': file_name,
            's3_key': s3_key,
            's3_bucket': S3_BUCKET,
            'created_at': created_at,
            'file_size': len(file_bytes)
        })

        print(f"✓ Saved research log: {log_id} for user {user_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Research log saved successfully',
                'log_id': log_id,
                'user_id': user_id,
                'research_title': research_title,
                'created_at': created_at,
                's3_key': s3_key
            })
        }
    except Exception as e:
        print(f"Save research log error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_research_logs(user_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get user's research logs sorted by date (newest first).

    Args:
        user_id: User's ID
        limit: Maximum number of logs to return

    Returns:
        Response with list of research logs
    """
    try:
        # Query using GSI to get logs sorted by created_at
        response = research_logs_table.query(
            IndexName='created_at-index',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,  # Descending order (newest first)
            Limit=limit
        )

        logs = response.get('Items', [])

        # Convert Decimal to number for JSON serialization
        logs = decimal_to_number(logs)

        print(f"✓ Retrieved {len(logs)} research logs for user {user_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'logs': logs,
                'count': len(logs)
            })
        }
    except Exception as e:
        print(f"Get research logs error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_research_log_file(user_id: str, log_id: str) -> Dict[str, Any]:
    """
    Get presigned URL to download research log file from S3.

    Args:
        user_id: User's ID
        log_id: Log ID

    Returns:
        Response with presigned download URL
    """
    try:
        # Get metadata from DynamoDB
        response = research_logs_table.get_item(
            Key={
                'user_id': user_id,
                'log_id': log_id
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Research log not found'})
            }

        log_item = response['Item']
        s3_key = log_item['s3_key']
        file_name = log_item['file_name']

        # Generate presigned URL (valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                'ResponseContentDisposition': f'attachment; filename="{file_name}"'
            },
            ExpiresIn=3600  # 1 hour
        )

        print(f"✓ Generated presigned URL for log {log_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'download_url': presigned_url,
                'file_name': file_name,
                'log_id': log_id
            })
        }
    except Exception as e:
        print(f"Get research log file error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def delete_research_log(user_id: str, log_id: str) -> Dict[str, Any]:
    """
    Delete research log from both DynamoDB and S3.

    Args:
        user_id: User's ID
        log_id: Log ID

    Returns:
        Response confirming deletion
    """
    try:
        # Get metadata from DynamoDB
        response = research_logs_table.get_item(
            Key={
                'user_id': user_id,
                'log_id': log_id
            }
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Research log not found'})
            }

        log_item = response['Item']
        s3_key = log_item['s3_key']

        # Delete from S3
        s3_client.delete_object(
            Bucket=S3_BUCKET,
            Key=s3_key
        )

        # Delete from DynamoDB
        research_logs_table.delete_item(
            Key={
                'user_id': user_id,
                'log_id': log_id
            }
        )

        print(f"✓ Deleted research log {log_id} for user {user_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Research log deleted successfully',
                'log_id': log_id
            })
        }
    except Exception as e:
        print(f"Delete research log error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handler(event, context):
    """Main Lambda handler."""
    try:
        # Parse request - handle both API Gateway and Function URL formats
        if isinstance(event.get('body'), str):
            # API Gateway format: body is a JSON string
            body = json.loads(event['body'])
        elif 'action' in event:
            # Function URL format: event is the direct payload
            body = event
        else:
            # Fallback
            body = event.get('body', {})

        action = body.get('action')

        if action == 'signup':
            return signup(
                body['email'],
                body['password'],
                body['organization'],
                body.get('name', '')
            )

        elif action == 'verify_email':
            return verify_email(body['email'], body['code'])

        elif action == 'login':
            return login(body['email'], body['password'])

        elif action == 'check_usage':
            return check_usage(body['user_id'])

        elif action == 'increment_usage':
            return increment_usage(body['user_id'], body['organization'])

        elif action == 'resend_verification':
            return resend_verification(body['email'])

        elif action == 'get_organizations':
            # Return available organizations (public info only)
            orgs_info = {
                code: {
                    'name': config['name'],
                    'description': config['description'],
                    'email_domains': config['email_domains']
                }
                for code, config in ORGANIZATIONS.items()
            }
            return {
                'statusCode': 200,
                'body': json.dumps({'organizations': orgs_info})
            }

        elif action == 'save_research_log':
            return save_research_log(
                body['user_id'],
                body['research_title'],
                body['research_question'],
                body['file_data'],
                body['file_name']
            )

        elif action == 'get_research_logs':
            return get_research_logs(
                body['user_id'],
                body.get('limit', 50)
            )

        elif action == 'get_research_log_file':
            return get_research_log_file(
                body['user_id'],
                body['log_id']
            )

        elif action == 'delete_research_log':
            return delete_research_log(
                body['user_id'],
                body['log_id']
            )

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }

    except Exception as e:
        print(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
