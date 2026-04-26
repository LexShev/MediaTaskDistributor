import os

import boto3
from botocore.client import Config

from planner.celery_settings import AWS_S3_ENDPOINT_URL,AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

s3_client = boto3.client(
    's3',
    endpoint_url=AWS_S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)
