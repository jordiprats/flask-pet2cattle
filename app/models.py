from botocore.client import Config

from datetime import datetime
from slugify import slugify

import markdown
import boto3
import math
import re
import os
import io

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
    raw_md = None

    def __init__(self, url, raw_md):
        self.raw_md = raw_md
        md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
        self.url = url
        self.html = md.convert(raw_md)
        self.metadata = md.Meta

    def is_published(self):
        try:
            if self.metadata['status'][0]=='published':
                date_now  = datetime.now()
                if self.publish_date() < date_now:
                    return True
        except:
            pass
        return False

    def publish_date(self):
        return datetime.strptime(self.metadata['date'][0], '%d/%m/%Y')
    
    def get_print_date(self):
        return self.metadata['date'][0]

    def get_keywords(self):
        try:
            keywords = []
            for keyword in self.metadata['keywords'][0].split(','):
                keywords.append(keyword.strip())
            return keywords
        except:
            return []

    def get_excerpt(self):
        buf = io.StringIO(self.raw_md)
        lines = buf.readlines(10000)

        excerpt = ''
        for line in lines:
            if re.match(r'^<!--.*-->$', line):
                break
            excerpt += line

        md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
        excerpt_html = md.convert(excerpt)

        return re.sub(r'<h1>.*</h1>', '', excerpt_html)

    def get_title(self):
        return self.metadata['title'][0]


    def __repr__(self):
        return self.url
    
    def __str__(self):
        return self.url

    def all(page=0, limit=5):
        global MINIO_BUCKET
        init_s3_client()

        response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix='posts', MaxKeys=1000)

        posts = []
        count=0
        get_key_value = lambda obj: obj['Key']
        for bucket_object in sorted(response['Contents'], key=get_key_value, reverse=True):
            if count >=(page*limit)+limit:
                break

            base_url = re.match(r'^posts(/[0-9]+/[0-9]+/).*\.md', bucket_object['Key'])
            if not base_url:
                continue
            url = base_url.groups()[0] + slugify(re.sub(r'^[0-9]+ ', '', re.sub(r'\.md$', '', re.sub(r'^posts/[0-9]+/[0-9]+/', '', bucket_object['Key']))))

            response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])
            post = Post(url, response['Body'].read().decode('utf-8'))

            if post.is_published():
                if count<page*limit:
                    count += 1
                    continue
                posts.append(post)
                count += 1

        data = {}
        data['Posts'] = posts
        data['page'] = math.ceil((count/5.0)-1)
        data['next'] = count >=(page*limit)+limit

        return data

    def filter(year, month, slug):
        global MINIO_BUCKET
        init_s3_client()

        response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix='posts/'+year+'/'+month, MaxKeys=1000)

        print(str(response))

        if not 'Contents' in response.keys():
            return []

        for bucket_object in response['Contents']:
            filename_slug = slugify(re.sub(r'^[0-9]+ ', '', re.sub(r'\.md$', '', bucket_object['Key'].lstrip('posts/'+year+'/'+month+'/'))))

            if slug == filename_slug:
                response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])

                return [ Post('/'+year+'/'+month+'/'+slug, response['Body'].read().decode('utf-8')) ]

        return []