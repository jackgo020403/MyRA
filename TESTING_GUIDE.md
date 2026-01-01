# 🧪 Testing Guide - Organization-Based Authentication

This guide walks you through testing the complete authentication system locally.

---

## 🚀 Quick Start

### Step 1: Start Docker Services
```bash
# Windows
start_local.bat

# Or manually:
docker-compose up -d
```

Wait for services to start (~30 seconds)

### Step 2: Create DynamoDB Tables
```bash
python aws-scripts\create_dynamodb_tables.py --local
```

You should see:
```
✅ Created table: myra-users-dev
✅ Created table: myra-usage-dev
✅ Created table: myra-verification-dev
✅ Created table: myra-organizations-dev
```

### Step 3: Run Automated Tests
```bash
python aws-scripts\test_lambda_org.py
```

Follow the prompts to complete email verification.

---

## 📋 What Gets Tested

### ✅ Organization Configuration
- 4 organizations: SNU_student, McKinsey, BCG, Bain
- Email domain validation for each org
- Different daily limits per org (SNU: 20, Consulting firms: 50)

### ✅ User Signup
1. **Valid email check**: Email must match organization domain
   - SNU: `@snu.ac.kr`
   - McKinsey: `@mckinsey.com`
   - BCG: `@bcg.com`
   - Bain: `@bain.com` or `@baincompany.com`

2. **Password hashing**: Using bcrypt for security

3. **Verification code generation**: 6-digit code, expires in 10 minutes

### ✅ Email Verification
- Verification code sent to console (in production, use AWS SES)
- Code validation
- Expiration handling
- Resend functionality

### ✅ Login
- Email + password authentication
- JWT token generation (7-day expiry)
- Organization-specific data in token
- Blocked if email not verified

### ✅ Usage Tracking
- Per-user daily search limits
- Organization-specific limits
- Increment/check usage
- Reset daily

---

## 🔍 Manual Testing Steps

### Test 1: Sign Up as SNU Student

```bash
# View Lambda logs in real-time
docker-compose logs -f lambda
```

In another terminal:
```bash
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"action\": \"signup\", \"email\": \"student@snu.ac.kr\", \"password\": \"test123\", \"organization\": \"SNU_student\", \"name\": \"Test Student\"}"
  }'
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Verification code sent to your email\", \"user_id\": \"user_SNU_student_...\", \"requires_verification\": true}"
}
```

**Check logs for verification code:**
```
=====================================
📧 VERIFICATION EMAIL
=====================================
To: student@snu.ac.kr
Subject: Verify your MyRA account - Seoul National University

Your verification code is: 123456

This code will expire in 10 minutes.
=====================================
```

### Test 2: Verify Email

```bash
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"action\": \"verify_email\", \"email\": \"student@snu.ac.kr\", \"code\": \"123456\"}"
  }'
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Email verified successfully\", \"token\": \"eyJ...\", \"daily_limit\": 20}"
}
```

### Test 3: Login

```bash
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"action\": \"login\", \"email\": \"student@snu.ac.kr\", \"password\": \"test123\"}"
  }'
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Login successful\", \"token\": \"eyJ...\", \"organization\": \"SNU_student\", \"daily_limit\": 20}"
}
```

### Test 4: Check Usage

```bash
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"action\": \"check_usage\", \"user_id\": \"user_SNU_student_1234567890\"}"
  }'
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"searches_used\": 0, \"daily_limit\": 20, \"remaining\": 20, \"can_search\": true}"
}
```

### Test 5: Increment Usage

```bash
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type": application/json" \
  -d '{
    "body": "{\"action\": \"increment_usage\", \"user_id\": \"user_SNU_student_1234567890\", \"organization\": \"SNU_student\"}"
  }'
```

---

## 🎨 Testing with Streamlit UI

### Step 1: Run Streamlit
```bash
streamlit run pages/1_🔐_Auth.py
```

### Step 2: Test Signup Flow
1. Click "Sign Up" tab
2. Enter:
   - Name: Test Student
   - Email: test@snu.ac.kr
   - Organization: Seoul National University (@snu.ac.kr)
   - Password: secure123
3. Click "Sign Up"
4. Check Docker logs for verification code:
   ```bash
   docker-compose logs lambda | grep "VERIFICATION" -A 10
   ```

### Step 3: Test Verification
1. Click "Verify Email" tab
2. Enter the 6-digit code from logs
3. Click "Verify"
4. Should redirect to main app with authentication

### Step 4: Test Login
1. Click "Login" tab
2. Enter email and password
3. Should see welcome message and redirect

---

## 🗄️ Viewing Database Contents

### Method 1: AWS CLI
```bash
# List all users
aws dynamodb scan \
  --table-name myra-users-dev \
  --endpoint-url http://localhost:8000 \
  --region us-east-1

# List verification codes
aws dynamodb scan \
  --table-name myra-verification-dev \
  --endpoint-url http://localhost:8000 \
  --region us-east-1

# List usage records
aws dynamodb scan \
  --table-name myra-usage-dev \
  --endpoint-url http://localhost:8000 \
  --region us-east-1
```

### Method 2: Python Script
```python
import boto3

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Get all users
users = dynamodb.Table('myra-users-dev')
response = users.scan()

for user in response['Items']:
    print(f"Email: {user['email']}")
    print(f"Organization: {user['organization']}")
    print(f"Verified: {user['email_verified']}")
    print(f"Daily Limit: {user['daily_limit']}")
    print("---")
```

---

## 🐛 Troubleshooting

### Verification code not showing
**Check Lambda logs:**
```bash
docker-compose logs lambda | tail -50
```

The code is printed to stdout since we're in local dev mode.

### "Table does not exist"
**Recreate tables:**
```bash
# Delete old tables
aws dynamodb delete-table --table-name myra-users-dev --endpoint-url http://localhost:8000
aws dynamodb delete-table --table-name myra-usage-dev --endpoint-url http://localhost:8000
aws dynamodb delete-table --table-name myra-verification-dev --endpoint-url http://localhost:8000

# Recreate
python aws-scripts\create_dynamodb_tables.py --local
```

### "Cannot connect to Docker"
**Check Docker is running:**
```bash
docker ps
```

If empty, start services:
```bash
docker-compose up -d
```

### Lambda not responding
**Rebuild container:**
```bash
docker-compose up -d --build lambda
```

### Email domain not validating
**Check organization config** in `lambda/config.py`:
- Ensure email domains are lowercase
- Check for typos
- Verify organization code matches

---

## ✅ Success Criteria

After running all tests, you should have:

1. ✅ 4 DynamoDB tables created
2. ✅ Multiple test users in different organizations
3. ✅ Verification codes generated and validated
4. ✅ JWT tokens issued after successful login
5. ✅ Usage tracking working per user
6. ✅ Organization-specific limits enforced

---

## 🔐 API Keys for Production

Before deploying to AWS, you need to set real API keys in your environment:

### For Local Testing (docker-compose.yml):
```yaml
environment:
  - ANTHROPIC_KEY_SNU=sk-ant-api03-...
  - SERPER_KEY_SNU=your-serper-key
  # Repeat for other orgs
```

### For AWS Lambda:
```bash
# Set environment variables in Lambda console
AWS_LAMBDA_FUNCTION=myra-auth

aws lambda update-function-configuration \
  --function-name $AWS_LAMBDA_FUNCTION \
  --environment "Variables={
    ANTHROPIC_KEY_SNU=sk-ant-api03-...,
    SERPER_KEY_SNU=your-key,
    ANTHROPIC_KEY_MCKINSEY=sk-ant-api03-...,
    SERPER_KEY_MCKINSEY=your-key
  }"
```

---

## 📚 Next Steps

1. ✅ Test local authentication
2. 🔄 Integrate auth with main Streamlit app
3. 🔄 Set up AWS SES for real email sending
4. 🔄 Deploy to AWS
5. 🔄 Add OAuth (Google/Microsoft) integration
6. 🔄 Add admin dashboard for user management

---

**Questions?** Check the logs or create an issue!
