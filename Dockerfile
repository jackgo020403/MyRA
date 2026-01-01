# Dockerfile for AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements
COPY lambda_requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/lambda_requirements.txt

# Copy function code
COPY lambda/ ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "auth.handler" ]
