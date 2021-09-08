from botocore.client import Config

from datetime import datetime
from slugify import slugify

import markdown
import boto3
import pytz
import math
import re
import os
import io

# global settings
MINIO_URL        = os.getenv('MINIO_URL', 'http://127.0.0.1:9000')
MINIO_BUCKET     = os.getenv('MINIO_BUCKET', 'pet2cattle')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'AKIAIOSFODNN7EXAMPLE')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

if os.getenv('DEBUG', False):
  DEBUG=True
else:
  DEBUG=False

if os.getenv('FORCE_PUBLISH', False):
  FORCE_PUBLISH=True
else:
  FORCE_PUBLISH=False

s3_client = None

def init_s3_client():
  global s3_client

  if not s3_client:
    try:
      if DEBUG:
        print("connecting: "+MINIO_URL)
      s3_client = boto3.client(
                    service_name='s3',
                    endpoint_url=MINIO_URL,
                    aws_access_key_id=MINIO_ACCESS_KEY,
                    aws_secret_access_key=MINIO_SECRET_KEY,
                    config=Config(signature_version='s3v4'),
                  )
    except:
      if DEBUG:
        print("ERROR: unable to connect to bucket")
      raise Exception('unable to connect to bucket')

class S3File:
  base_object = None
  url = None
  last_modified = None

  def __init__(self, base_object, url, last_modified=None):
    self.base_object = base_object
    self.url = url
    self.last_modified = last_modified
  
  def get_url(self):
    return self.url

  def get_data(self):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    return s3_client.get_object(Bucket=MINIO_BUCKET, Key=self.base_object+'/'+self.url)['Body']

  def exists(self):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    try:
      return s3_client.head_object(Bucket=MINIO_BUCKET, Key=self.base_object+'/'+self.url)
    except:
      return False

  def save(self, filehandle):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    response = s3_client.put_object(
                      Body=filehandle,
                      Bucket=MINIO_BUCKET,
                      Key=self.base_object+'/'+self.url
                    )   

  def __repr__(self):
    return self.url
  
  def __str__(self):
    return self.url

class Static(S3File):
  filehandle = None
  def __init__(self, url, last_modified, filehandle):
    super().__init__('static', url, last_modified)
    self.filehandle = filehandle
  
  def save(self):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    response = s3_client.put_object(
                      Body=self.filehandle,
                      Bucket=MINIO_BUCKET,
                      Key=self.base_object+'/'+self.url
                    )

class Sitemap(S3File):
  filehandle = None
  def __init__(self, url, last_modified, filehandle):
    super().__init__('sitemaps', url, last_modified)
    self.filehandle = filehandle
  
  def save(self):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    response = s3_client.put_object(
                      Body=self.filehandle,
                      Bucket=MINIO_BUCKET,
                      Key=self.base_object+'/'+self.url
                    )

class Page(S3File):
  html = None
  metadata = None
  raw_md = None
  bucket_prefix = 'pages'
  read_time = 2

  def get_read_time(self):
    return self.read_time

  def refresh_markdown(self):
    md = markdown.Markdown(tab_length=2, extensions=['markdown.extensions.codehilite', 'markdown.extensions.fenced_code', 'markdown.extensions.meta', 'markdown.extensions.toc'])
    self.read_time = (len(self.raw_md.split())//200)+1

    self.html = md.convert(self.raw_md).replace('</h1>','</h1><p class="text-secondary" >'+str(self.read_time)+' min read</p>')
    
    self.metadata = md.Meta

  def __init__(self, url, raw_md, last_modified, bucket_prefix='pages'):
    self.bucket_prefix = bucket_prefix
    super().__init__(self.bucket_prefix, url, last_modified)
    self.raw_md = raw_md

    self.refresh_markdown()

    try:
      if not self.metadata['image']:
        raise Exception("image empty")
    except:
      print(str(self.metadata))
      try:
        # TODO: check other default paths?
        for category in self.metadata['categories']:
          category_image = S3File('static', 'categories/'+category.lower()+'_small.jpg')
          if category_image.exists():
            self.metadata['image'] = "https://static.pet2cattle.com/"+category_image.url
      except:
        pass

  def is_page(self):
      return True

  def is_published(self):
    if FORCE_PUBLISH:
      return True
    try:
      if self.metadata['status'][0]=='published':
        if self.is_page():
          return True
        else:
          date_now  = datetime.now()
          if self.publish_date() < date_now:
            return True
    except:
      pass
    return False

  def get_last_modified(self):
    publish_date = self.publish_date()

    if not publish_date or self.last_modified > publish_date.replace(tzinfo=pytz.UTC):
      return self.last_modified
    else:
      return publish_date.replace(tzinfo=pytz.UTC)

  def publish_date(self):
    try:
      date = datetime.strptime(self.metadata['date'][0], '%d/%m/%Y')
    except Exception as e:
      if DEBUG:
        print(str(e))
      try:
        date = datetime.strptime(self.metadata['date'][0], '%-d/%-m/%Y')
      except Exception as e:
        if DEBUG:
          print(str(e))
        return None
    return date
  
  def get_print_date(self):
    try:
      return self.publish_date().strftime("%d/%m/%Y")
    except:
      return ''

  def get_keywords(self):
    try:
      keywords = []
      for keyword in self.metadata['keywords'][0].split(','):
        keywords.append(keyword.strip())
      return keywords
    except:
      return []

  def get_categories(self):
    try:
      keywords = []
      for keyword in self.metadata['categories'][0].split(','):
        keywords.append(keyword.strip())
      return keywords
    except:
      return []

  def get_tags(self):
    try:
      keywords = []
      for keyword in self.metadata['tags'][0].split(','):
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

    md = markdown.Markdown(tab_length=2, extensions=['markdown.extensions.codehilite', 'markdown.extensions.fenced_code', 'markdown.extensions.meta'])

    excerpt_html = md.convert(excerpt)

    return re.sub(r'<h1>.*</h1>', '', excerpt_html)

  def get_title(self):
    try:
      buf = io.StringIO(self.raw_md)
      lines = buf.readlines(10000)

      for line in lines:
        if re.match(r'^# ', line):
          return re.sub(r'^# ', '', line)
    except:
      pass
    return self.metadata['title'][0]

  def filter(url):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=Page.bucket_prefix+'/', MaxKeys=1000)

    if not 'Contents' in response.keys():
      return []

    for bucket_object in response['Contents']:
      filename_slug = ''
      items = re.sub(r'pages/', '', re.sub(r'\.md$', '', bucket_object['Key'])).split('/')
      for item in items:
        filename_slug += '/'+slugify(item)
      if url == filename_slug:
        response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])
        return [ Page(url, response['Body'].read().decode('utf-8'), response['LastModified']) ]

    return []
  
  def urls():
    global MINIO_BUCKET, s3_client, DEBUG
    init_s3_client()

    # no hi hauria d'haver més de 1000 pàgines (ni 50 de fet)
    response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=Page.bucket_prefix, MaxKeys=1000)

    pages = []
    get_key_value = lambda obj: obj['Key']
    for bucket_object in sorted(response['Contents'], key=get_key_value, reverse=True):
      tokenized = re.sub(r'^'+Page.bucket_prefix+r'/', '', bucket_object['Key']).split('/')
      if len(tokenized) > 2:
        if DEBUG:
          print('skipping '+bucket_object['Key'])
        continue
      
      if len(tokenized) == 2:
        url = slugify(tokenized[0])+'/'+slugify(re.sub(r'\.md$', '', tokenized[1]))
      else:
        url = slugify(re.sub(r'\.md$', '', tokenized[0]))

      page_response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])
      page = Page(url, page_response['Body'].read().decode('utf-8'), page_response['LastModified'])

      if page.is_published():
        pages.append(url)

    return pages

class Post(Page):
  bucket_prefix = 'posts'

  def is_page(self):
    return False

  def __init__(self, url, raw_md, last_modified):
    super().__init__( url, raw_md, last_modified, Post.bucket_prefix)

  def all(page=0, limit=5, prefix=None):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    if prefix:
      s3_prefix = Post.bucket_prefix+prefix
    else:
      s3_prefix = Post.bucket_prefix

    data = {}
    data['next'] = False

    # TODO: arreglar limit de 1000 objectes
    response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=s3_prefix, MaxKeys=1000)

    posts = []
    count=0
    get_key_value = lambda obj: obj['Key']
    for bucket_object in sorted(response['Contents'], key=get_key_value, reverse=True):

      base_url = re.match(r'^'+Post.bucket_prefix+r'(/[0-9]+/[0-9]+/).*\.md', bucket_object['Key'])
      if not base_url:
        continue
      url = base_url.groups()[0] + slugify(re.sub(r'^[0-9]+ ', '', re.sub(r'\.md$', '', re.sub(r'^'+Post.bucket_prefix+r'/[0-9]+/[0-9]+/', '', bucket_object['Key']))))

      response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])
      post = Post(url, response['Body'].read().decode('utf-8'), response['LastModified'])

      if post.is_published():
        if limit>=0 and count >=(page*limit)+limit:
          # N+1 for checking next whether there are more posts
          data['next'] = True
          break
        if limit>=0 and count<page*limit:
          count += 1
          continue

        posts.append(post)
        count += 1

    data['Posts'] = posts
    data['page'] = math.ceil((count/5.0)-1)

    return data

  def getURL(url):
    url_parts = re.match(r'^/([0-9]{4})/([0-9]{2})/([^/]*)$', url)

    if url_parts:
      return Post.filter(url_parts.groups()[0], url_parts.groups()[1], url_parts.groups()[2])
    else:
      return []

  def filter(year, month, slug):
    global MINIO_BUCKET, s3_client
    init_s3_client()

    response = s3_client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=Post.bucket_prefix+'/'+str(year)+'/'+str(month), MaxKeys=1000)

    if not 'Contents' in response.keys():
      return []

    for bucket_object in response['Contents']:
      filename_slug = slugify(re.sub(r'^[0-9]+ ', '', re.sub(r'\.md$', '', bucket_object['Key'].lstrip(Post.bucket_prefix+'/'+str(year)+'/'+str(month)+'/'))))

      if slug == filename_slug:
        response = s3_client.get_object(Bucket=MINIO_BUCKET, Key=bucket_object['Key'])

        return [ Post('/'+year+'/'+month+'/'+slug, response['Body'].read().decode('utf-8'), response['LastModified']) ]

    return []