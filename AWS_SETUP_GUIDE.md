# AWS Lambda + DynamoDB Setup Guide

This guide shows you how to develop, test, and deploy AWS Lambda functions locally using Docker, then push to AWS.

## 🎯 What You Can Do

1. **Local Development**: Run Lambda + DynamoDB on your machine with Docker
2. **Test Locally**: Test authentication, signup, login without touching AWS
3. **Push to AWS**: Deploy Lambda functions and DynamoDB tables to production

---

## 📋 Prerequisites

### Required Software
- ✅ Docker Desktop installed and running
- ✅ AWS CLI installed (`pip install awscli`)
- ✅ AWS account with credentials configured

### AWS Credentials Setup
```bash
# Configure AWS credentials
aws configure

# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

---

## 🚀 Quick Start - Local Development

### Step 1: Start Docker Services
```bash
# Start DynamoDB Local + Lambda container
docker-compose up -d

# Check services are running
docker-compose ps
```

You should see:
- `myra-dynamodb-local` on port 8000
- `myra-lambda` on port 9000

### Step 2: Create DynamoDB Tables Locally
```bash
# Create tables in LOCAL DynamoDB
python aws-scripts/create_dynamodb_tables.py --local
```

This creates:
- `myra-users-dev` - User accounts
- `myra-usage-dev` - Usage tracking

### Step 3: Test Lambda Function Locally
```bash
# Run tests against local Lambda
python aws-scripts/test_lambda_local.py
```

This tests:
- ✅ User signup
- ✅ User login
- ✅ Usage checking
- ✅ Usage increment

### Step 4: Access DynamoDB Local (Optional)
```bash
# Install DynamoDB admin UI
npm install -g dynamodb-admin

# Run admin UI
DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin

# Open: http://localhost:8001
```

---

## ☁️ Deploy to AWS Production

### Step 1: Create DynamoDB Tables in AWS
```bash
# Create production tables in AWS
python aws-scripts/create_dynamodb_tables.py
```

This creates:
- `myra-users-prod` - User accounts (AWS)
- `myra-usage-prod` - Usage tracking (AWS)

### Step 2: Create IAM Role for Lambda

Go to AWS Console → IAM → Roles → Create Role:

1. **Trusted entity**: Lambda
2. **Permissions**: Attach these policies:
   - `AWSLambdaBasicExecutionRole`
   - `AmazonDynamoDBFullAccess` (or create custom policy)
3. **Role name**: `lambda-execution-role`
4. **Copy the Role ARN** (needed for deployment)

### Step 3: Deploy Lambda Function
```bash
# Build Docker image, push to ECR, create/update Lambda
python aws-scripts/deploy_lambda.py
```

This will:
1. Create ECR repository
2. Build Docker image
3. Push to ECR
4. Create/update Lambda function

### Step 4: Configure Lambda Function URL (Optional)

If you want to call Lambda directly via HTTPS:

1. Go to AWS Console → Lambda → Functions → `myra-auth`
2. Configuration → Function URL → Create function URL
3. Auth type: `NONE` (or `AWS_IAM` for security)
4. Copy the function URL

---

## 🧪 Testing

### Test Local Lambda
```bash
# Make sure Docker is running
docker-compose up -d

# Run tests
python aws-scripts/test_lambda_local.py
```

### Test AWS Lambda
```bash
# Install boto3 if not already
pip install boto3

# Test using AWS Lambda invoke
python -c "
import boto3
import json

client = boto3.client('lambda', region_name='us-east-1')

response = client.invoke(
    FunctionName='myra-auth',
    Payload=json.dumps({
        'body': json.dumps({
            'action': 'signup',
            'email': 'test@example.com',
            'password': 'secure123'
        })
    })
)

print(json.loads(response['Payload'].read()))
"
```

### Test via Function URL
```bash
# Replace with your function URL
curl -X POST https://YOUR-FUNCTION-URL.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"action\": \"signup\", \"email\": \"test@example.com\", \"password\": \"secure123\"}"
  }'
```

---

## 📂 File Structure

```
MyRA/
├── Dockerfile                          # Lambda container definition
├── docker-compose.yml                  # Local dev environment
├── lambda_requirements.txt             # Lambda dependencies
├── lambda/
│   └── auth.py                        # Authentication Lambda function
├── aws-scripts/
│   ├── create_dynamodb_tables.py      # Create DynamoDB tables
│   ├── deploy_lambda.py               # Deploy to AWS
│   └── test_lambda_local.py           # Test local Lambda
└── AWS_SETUP_GUIDE.md                 # This file
```

---

## 🔧 Common Commands

### Docker Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f lambda
docker-compose logs -f dynamodb-local

# Rebuild Lambda container after code changes
docker-compose up -d --build lambda
```

### DynamoDB Management
```bash
# List tables (local)
aws dynamodb list-tables --endpoint-url http://localhost:8000

# List tables (AWS)
aws dynamodb list-tables --region us-east-1

# Scan table (local)
aws dynamodb scan --table-name myra-users-dev --endpoint-url http://localhost:8000

# Delete table (local)
aws dynamodb delete-table --table-name myra-users-dev --endpoint-url http://localhost:8000
```

### Lambda Management
```bash
# List Lambda functions
aws lambda list-functions --region us-east-1

# Get Lambda function details
aws lambda get-function --function-name myra-auth --region us-east-1

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name myra-auth \
  --environment "Variables={JWT_SECRET=your-secret-here}" \
  --region us-east-1
```

---

## 🔐 Security Best Practices

1. **JWT Secret**: Change `JWT_SECRET` environment variable in production
   ```bash
   # Generate secure random secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **IAM Roles**: Use least-privilege policies for Lambda
   - Only grant DynamoDB access to specific tables
   - Use resource-based policies

3. **API Gateway**: Add authentication to Lambda function URL
   - Use AWS_IAM auth type
   - Or add API Gateway with Cognito

4. **Secrets Manager**: Store sensitive data in AWS Secrets Manager
   - API keys (Anthropic, Serper)
   - JWT secret
   - Database credentials

---

## 💡 Next Steps

1. ✅ Test locally with Docker
2. ✅ Deploy to AWS
3. 🔄 Integrate with Streamlit app
4. 🔄 Add API Gateway for better routing
5. 🔄 Add forgot password functionality
6. 🔄 Add email verification

---

## ❓ Troubleshooting

### Docker issues
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop if needed
```

### Lambda can't connect to DynamoDB
```bash
# Check endpoint URL in environment variables
docker-compose exec lambda env | grep DYNAMO

# Should show: DYNAMODB_ENDPOINT=http://dynamodb-local:8000
```

### AWS credentials not working
```bash
# Check credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### Port already in use
```bash
# Stop services using ports 8000 or 9000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

---

## 📚 Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Docker Documentation](https://docs.docker.com/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
