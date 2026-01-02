"""
Deploy Lambda function to AWS.
Builds Docker image and pushes to ECR, then updates Lambda.

Prerequisites:
1. AWS CLI configured with credentials
2. Docker running
3. ECR repository created

Run with: python aws-scripts/deploy_lambda.py
"""
import boto3
import subprocess
import os

# Configuration
AWS_REGION = 'ap-northeast-2'
ECR_REPO_NAME = 'myra-lambda'
LAMBDA_FUNCTION_NAME = 'myra-auth'
AWS_ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']

ECR_REPO_URI = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO_NAME}"


def run_command(cmd, description):
    """Run shell command and handle errors."""
    print(f"\n[RUNNING] {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return False

    print(f"[OK] {description} completed")
    return True


def create_ecr_repo():
    """Create ECR repository if it doesn't exist."""
    ecr = boto3.client('ecr', region_name=AWS_REGION)

    try:
        ecr.create_repository(
            repositoryName=ECR_REPO_NAME,
            imageScanningConfiguration={'scanOnPush': True}
        )
        print(f"[OK] Created ECR repository: {ECR_REPO_NAME}")
    except ecr.exceptions.RepositoryAlreadyExistsException:
        print(f"[WARN] ECR repository {ECR_REPO_NAME} already exists")


def build_and_push():
    """Build Docker image and push to ECR."""
    # Login to ECR
    login_cmd = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    if not run_command(login_cmd, "Login to ECR"):
        return False

    # Build and push image with correct platform for Lambda
    # Using buildx to avoid manifest issues with Lambda
    build_push_cmd = f"docker buildx build --platform linux/amd64 --provenance=false --sbom=false -t {ECR_REPO_URI}:latest --push ."
    if not run_command(build_push_cmd, "Build and push Docker image"):
        return False

    return True


def create_or_update_lambda():
    """Create or update Lambda function."""
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)

    function_config = {
        'FunctionName': LAMBDA_FUNCTION_NAME,
        'Role': f'arn:aws:iam::{AWS_ACCOUNT_ID}:role/lambda-execution-role',  # Must exist
        'Code': {'ImageUri': f"{ECR_REPO_URI}:latest"},
        'PackageType': 'Image',
        'Timeout': 30,
        'MemorySize': 512,
        'Environment': {
            'Variables': {
                'DYNAMODB_TABLE_USERS': 'myra-users-prod',
                'DYNAMODB_TABLE_USAGE': 'myra-usage-prod',
                'JWT_SECRET': os.environ.get('JWT_SECRET', 'CHANGE-ME-IN-AWS-CONSOLE')
            }
        }
    }

    try:
        # Try to create new function
        lambda_client.create_function(**function_config)
        print(f"[OK] Created Lambda function: {LAMBDA_FUNCTION_NAME}")
    except lambda_client.exceptions.ResourceConflictException:
        # Function exists, update it
        lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ImageUri=f"{ECR_REPO_URI}:latest"
        )
        print(f"[OK] Updated Lambda function: {LAMBDA_FUNCTION_NAME}")


if __name__ == '__main__':
    print("Deploying Lambda function to AWS...\n")

    print("Step 1: Create ECR repository")
    create_ecr_repo()

    print("\nStep 2: Build and push Docker image")
    if not build_and_push():
        print("\n[ERROR] Deployment failed!")
        exit(1)

    print("\nStep 3: Create/update Lambda function")
    create_or_update_lambda()

    print("\nDeployment complete!\n")
    print(f"Lambda function: {LAMBDA_FUNCTION_NAME}")
    print(f"ECR image: {ECR_REPO_URI}:latest")
    print(f"Region: {AWS_REGION}")
    print()
