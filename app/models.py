from botocore.client import Config

import boto3

# global settings
MINIO_URL        = os.getenv('MINIO_URL', None)
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', None)
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', None)

s3_client = None

def init_s3_client():
    global s3_client

    if not s3_client:
        s3_client = boto3.client(
                                    service_name='s3',
                                    endpoint_url=MINIO_URL,
                                    aws_access_key_id=MINIO_ACCESS_KEY,
                                    aws_secret_access_key=MINIO_SECRET_KEY,
                                    config=Config(signature_version='s3v4'),
                                )