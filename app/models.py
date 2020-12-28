from botocore.client import Config

from datetime import datetime
from slugify import slugify

import markdown
import boto3
import re
import os

# global settings
MINIO_URL        = os.getenv('MINIO_URL', 'http://127.0.0.1:9000')
MINIO_BUCKET     = os.getenv('MINIO_BUCKET', 'demo')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'AKIAIOSFODNN7EXAMPLE')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

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

class Post:
    url = None
    html = None
    metadata = None

    def __init__(self, url, raw_md):
        md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
        self.url = url
        self.html = md.convert(raw_md)
        self.metadata = md.Meta

    def is_published(self):
        if self.metadata['status'][0]=='published':
            date_now  = datetime.now()
            if self.publish_date() < date_now:
                return True
        return False

    def publish_date(self):
        return datetime.strptime(self.metadata['date'][0], '%d/%m/%Y')

    def get_keywords(self):
        try:
            keywords = []
            for keyword in self.metadata['keywords'][0].split(','):
                keywords.append(keyword.strip())
            return keywords
        except:
            return []

    def filter(year, month, slug):
        global MINIO_BUCKET
        init_s3_client()

        response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix='posts/'+year+'/'+month, MaxKeys=100)

        print(str(response))

        if not 'Contents' in response.keys():
            return []

        for bucket_object in response['Contents']:
            filename_slug = slugify(re.sub(r'^[0-9]+ ', '', re.sub(r'\.md$', '', bucket_object['Key'].lstrip('posts/'+year+'/'+month+'/'))))

            if slug == filename_slug:
                response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])

                return [ Post('/'+year+'/'+month+'/'+slug, response['Body'].read().decode('utf-8')) ]

        return []