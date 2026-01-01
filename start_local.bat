@echo off
echo ========================================
echo   MyRA - Local Development Setup
echo ========================================
echo.

echo Step 1: Starting Docker services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Docker failed to start. Make sure Docker Desktop is running!
    pause
    exit /b 1
)
echo.

echo Step 2: Waiting for services to initialize...
timeout /t 5 /nobreak > nul
echo.

echo Step 3: Creating DynamoDB tables...
python aws-scripts\create_dynamodb_tables.py --local
if %errorlevel% neq 0 (
    echo ERROR: Failed to create tables. Make sure Python and boto3 are installed!
    pause
    exit /b 1
)
echo.

echo Step 4: Running tests...
python aws-scripts\test_lambda_local.py
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Your local environment is ready:
echo   - DynamoDB Local: http://localhost:8000
echo   - Lambda API: http://localhost:9000
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause
