# 🚀 Docker + AWS Lambda Quick Start

This guide gets you up and running with local Lambda development in **5 minutes**.

---

## ✅ Prerequisites

1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
   - Windows: Docker Desktop for Windows
   - Mac: Docker Desktop for Mac
   - Linux: Docker Engine

2. **Python 3.9+** with pip

3. **Install Python dependencies**:
   ```bash
   pip install boto3 requests PyJWT bcrypt
   ```

---

## 🎯 Quick Start (Windows)

### Option 1: Automated Script
```bash
# Double-click this file or run:
start_local.bat
```

This will:
- ✅ Start Docker Compose (DynamoDB + Lambda)
- ✅ Create DynamoDB tables
- ✅ Run tests automatically

### Option 2: Manual Steps
```bash
# 1. Start services
docker-compose up -d

# 2. Create tables
python aws-scripts\create_dynamodb_tables.py --local

# 3. Test Lambda
python aws-scripts\test_lambda_local.py
```

---

## 🎯 Quick Start (Mac/Linux)

```bash
# 1. Start services
docker-compose up -d

# 2. Create tables
python aws-scripts/create_dynamodb_tables.py --local

# 3. Test Lambda
python aws-scripts/test_lambda_local.py
```

---

## 🧪 What Gets Tested

The test script (`test_lambda_local.py`) automatically tests:

1. **✅ User Signup**
   ```json
   {
     "action": "signup",
     "email": "test@example.com",
     "password": "secure123"
   }
   ```

2. **✅ User Login**
   ```json
   {
     "action": "login",
     "email": "test@example.com",
     "password": "secure123"
   }
   ```

3. **✅ Check Usage**
   ```json
   {
     "action": "check_usage",
     "user_id": "user_123456"
   }
   ```

4. **✅ Increment Usage**
   ```json
   {
     "action": "increment_usage",
     "user_id": "user_123456"
   }
   ```

---

## 📊 What You Get

### Services Running:
- **DynamoDB Local**: `http://localhost:8000`
  - Tables: `myra-users-dev`, `myra-usage-dev`
  - Persistent data stored in Docker volume

- **Lambda Function**: `http://localhost:9000`
  - Endpoint: `/2015-03-31/functions/function/invocations`
  - Simulates AWS Lambda runtime

### Database Schema:

**myra-users-dev**
```
{
  "email": "user@example.com",          // Primary Key
  "user_id": "user_1234567890.123",     // Global Secondary Index
  "password_hash": "bcrypt_hash",
  "created_at": "2025-01-01T12:00:00",
  "daily_limit": 10,
  "plan": "free"
}
```

**myra-usage-dev**
```
{
  "user_id": "user_1234567890.123",     // Partition Key
  "date": "2025-01-01",                  // Sort Key
  "searches_used": 5
}
```

---

## 🔍 Viewing Your Data

### Method 1: AWS CLI
```bash
# List all users (local)
aws dynamodb scan \
  --table-name myra-users-dev \
  --endpoint-url http://localhost:8000

# Check user usage (local)
aws dynamodb scan \
  --table-name myra-usage-dev \
  --endpoint-url http://localhost:8000
```

### Method 2: DynamoDB Admin UI
```bash
# Install
npm install -g dynamodb-admin

# Run
DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin

# Open browser: http://localhost:8001
```

### Method 3: Python Script
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
table = dynamodb.Table('myra-users-dev')
response = table.scan()
print(response['Items'])
```

---

## 🛠️ Development Workflow

### 1. Make Code Changes
Edit `lambda/auth.py` with your changes

### 2. Rebuild Lambda Container
```bash
# Rebuild and restart
docker-compose up -d --build lambda
```

### 3. Test Changes
```bash
python aws-scripts\test_lambda_local.py
```

### 4. View Logs
```bash
# View Lambda logs
docker-compose logs -f lambda

# View all logs
docker-compose logs -f
```

---

## 🧹 Cleanup

### Stop Services (Keep Data)
```bash
docker-compose down
```

### Stop Services + Delete Data
```bash
docker-compose down -v
```

### Delete Everything
```bash
# Stop containers
docker-compose down -v

# Remove images
docker rmi myra-lambda
docker rmi amazon/dynamodb-local
```

---

## 🐛 Troubleshooting

### "Cannot connect to Docker daemon"
**Solution**: Start Docker Desktop and wait for it to fully initialize

### "Port 8000 already in use"
**Solution**: Another service is using port 8000
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### "Module not found: boto3"
**Solution**: Install Python dependencies
```bash
pip install boto3 requests PyJWT bcrypt
```

### "Table already exists"
**Solution**: This is normal - the script detects existing tables

### Lambda not responding
**Solution**: Check if container is running
```bash
docker-compose ps

# Should show both services as "Up"
# If not, check logs:
docker-compose logs lambda
```

---

## ☁️ Deploy to AWS Production

Once your local testing is complete:

```bash
# 1. Create production DynamoDB tables
python aws-scripts/create_dynamodb_tables.py

# 2. Deploy Lambda to AWS
python aws-scripts/deploy_lambda.py
```

See [AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md) for detailed AWS deployment instructions.

---

## 📚 Next Steps

1. ✅ Get local development working
2. ✅ Test Lambda functions locally
3. 🔄 Integrate with Streamlit app (coming next)
4. 🔄 Add API Gateway
5. 🔄 Deploy to AWS production

---

## 💡 Pro Tips

- **Keep Docker running**: Services start faster when Docker is already running
- **Use volumes**: Data persists between restarts in `dynamodb-data` volume
- **Check logs often**: `docker-compose logs -f` shows real-time debugging info
- **Test locally first**: Always test changes locally before deploying to AWS
- **Use .env files**: Store secrets in `.env` file (don't commit to git!)

---

## 🎓 Learning Resources

- **Docker Compose**: https://docs.docker.com/compose/
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **DynamoDB**: https://docs.aws.amazon.com/dynamodb/
- **boto3**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

**Questions?** Check the [AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md) for more details!
