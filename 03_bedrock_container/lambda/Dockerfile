FROM public.ecr.aws/lambda/python:3.11

# Copy and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy your handler code into the Lambda task root
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the Lambda handler (module.function)
CMD ["handler.handler"]
