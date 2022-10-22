
from flaskext.markdown import Markdown
from flask_caching import Cache

from flask import send_from_directory
from flask import render_template
from flask import make_response
from flask import redirect
from flask import request
from flask import abort

from whoosh.filedb.filestore import FileStorage
from whoosh import index

from slugify import slugify

from app import models
from app import app

import datetime
import pickle
import yaml
import re
import os

if os.getenv('DEBUG', False):
  DEBUG=True
else:
  DEBUG=False

if os.getenv('FORCE_PUBLISH', False):
  FORCE_PUBLISH=True
else:
  FORCE_PUBLISH=False

if DEBUG:
  CACHE_TYPE = "null"
else:
  CACHE_TYPE = "filesystem"

CANONICAL_DOMAIN = os.getenv('CANONICAL_DOMAIN', 'https://pet2cattle.com')

config = {
  "DEBUG": DEBUG,
  "CACHE_TYPE": CACHE_TYPE,
  "CACHE_DEFAULT_TIMEOUT": 300,
  'CACHE_DIR': os.getenv('CACHE_DIR', 'cache')
}

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config.from_mapping(config)
cache = Cache(app)
cache.clear()

md = Markdown(app,
        extensions=['meta'],
        safe_mode=True,
        output_format='html4',
       )

FULLTEXT_INDEX_PATH = os.getenv('FULLTEXT_INDEX_PATH', "whoosh")

search_enabled = False
try:
  if not os.path.exists(FULLTEXT_INDEX_PATH):
      os.makedirs(FULLTEXT_INDEX_PATH, exist_ok=True)

  if index.exists_in(FULLTEXT_INDEX_PATH):
    search_enabled = True
    storage = FileStorage(FULLTEXT_INDEX_PATH)
    fulltext_index = storage.open_index()
except Exception as e:
  if DEBUG:
    print('whoosh index error: '+str(e))
  pass

ENABLE_SEARCH_BAR = os.getenv('ENABLE_SEARCH_BAR', False)

if ENABLE_SEARCH_BAR:
  # force enable search bar - whoosh might fail
  search_enabled = True

if DEBUG:
  print('search_enabled: '+str(search_enabled))

@cache.cached(timeout=86400, key_prefix="get_archives")
def get_archives():
  try:
    return pickle.loads(models.S3File('indexes', 'archives.dict').get_data().read())
  except:
    return {}

@cache.cached(timeout=3600, key_prefix="get_webindex_page")
def get_webindex_page():
  try:
    return pickle.loads(models.S3File('indexes', 'webindex.dict').get_data().read())
  except:
    return None

@cache.cached(timeout=7200, key_prefix="get_related_categories")
def get_related_categories(category):
  try:
    if DEBUG:
      print("get_related_categories")
    related_categories = [ pickle.loads(models.S3File('indexes', 'cat2relatedcats.dict').get_data().read())[slugify(category)][related_cat] for related_cat in pickle.loads(models.S3File('indexes', 'cat2relatedcats.dict').get_data().read())[slugify(category)].keys() ]
    return related_categories
  except Exception as e:
    if DEBUG:
      print(str(e))
    return None

@cache.cached(timeout=86400, key_prefix="get_navigation")
def get_navigation():
  if DEBUG:
    print('get_navigation')

  page_urls = models.Page.urls()

  nav = {}

  for page_url in page_urls:
    if '/' in page_url:
      # TODO: definir una manera de ordernar categories/pagines
      # [
      #     [['terraform', 'hashicorp-certified-terraform-associate'], 'HashiCorp Certified Terraform Associate Study Guide\n'], 
      #     [['kubernetes', 'object-reference'], 'Kubernetes Object reference\n'], 
      #     [['kubernetes', 'kubectl-reference'], 'kubectl reference'], 
      #     [['kubernetes', 'cka'], 'Certified Kubernetes Administrator Study Guide\n'], 
      #     ['about', 'About pet2cattle\n'], 
      #     [['aws', 'certified-solutions-architect-associate-saa-c02'], 'AWS Certified Solutions Architect Associate SAA-C02\n']
      # ]
      category = page_url.split('/')[0]
      page = page_url.split('/')[1]

      if category not in nav.keys():
        nav[category] = { 'is_page': False, 'subpages': [] }

      nav[category]['subpages'].append({ 'is_page': True, 'url': '/'+category+'/'+page, 'title': models.Page.filter('/'+page_url)[0].get_short_title() })
    else:
      rel=""
      try:
        page = models.Page.filter(page_url)[0]
        if "noindex" in page.metadata['robots']:
          rel="nofollow"
      except:
        pass
      nav[page_url] = { 'is_page': True, 'url': '/'+page_url, 'title': models.Page.filter('/'+page_url)[0].get_title(), 'rel': rel }

  return nav

#
# ROUTES
#

@app.route('/crd-generator/')
def crd_generator():
  if DEBUG:
    print('CRD generator')

  page_metadata={}
  page_metadata['title']=['Kubernetes: Object to CRD']
  page_metadata['robots']='index,follow'
  page_metadata['keywords']=['kubernetes', 'CRD', 'generator']
  page_metadata['categories']=['Kubernetes']
  page_metadata['tags']=['CRD']
  page_metadata['summary']=['Create CRD definitions based on sample objects']

  return render_template('k8s2crd.html', 
                    post_metadata=page_metadata, 
                    page_url='https://pet2cattle.com',
                    tags=page_metadata['tags'],
                    categories=page_metadata['categories'],
                    navigation=get_navigation(),
                    search_enabled=search_enabled
                  )

@app.route('/mysql-memory-online-calculator/')
def mysql_calculator():
  if DEBUG:
    print('MySQL calculator')

  page_metadata={}
  page_metadata['title']=['MySQL: Max memory online calculator']
  page_metadata['robots']='index,follow'
  page_metadata['keywords']=['MySQL', 'online', 'calculator', 'memory']
  page_metadata['categories']=['MySQL']
  page_metadata['tags']=['memory']
  page_metadata['summary']=['Calculate the maximum amount of memory a MySQL instance can consume']

  return render_template('k8s2crd.html', 
                    post_metadata=page_metadata, 
                    page_url='https://pet2cattle.com',
                    tags=page_metadata['tags'],
                    categories=page_metadata['categories'],
                    navigation=get_navigation(),
                    search_enabled=search_enabled
                  )

@app.route('/search/', defaults={'page': 0})
@app.route('/search/page/<int:page>')
def search(page):
  if DEBUG:
    print('search')
  try:
    search_string = request.args.get('s').lower()
  except:
    search_string = ""

  page_metadata={}
  page_metadata['title']=['From pet to cattle']
  page_metadata['robots']='noindex,follow'
  page_metadata['keywords']=[' '.join(search_string)]
  page_metadata['summary']=['Treat your clusters like cattle, not pets by using kubernetes, helm and terraform']

  response = cache.get("search_full_text_"+search_string)
  if not response:
    response = models.Post.search(search_string, fulltext_index, page, 5)
    cache.set("search_full_text_"+search_string, response)

  if len(response['Posts'])==0:
    if DEBUG:
      print('empty')
    response = cache.get("search_full_text_pet2cattle")
    if not response:
      response = models.Post.search('pet2cattle', fulltext_index, page, 5)
      cache.set("search_full_text_pet2cattle", response)

  return render_template('index.html', 
                    single=False,
                    posts=response['Posts'], 
                    post_metadata=page_metadata, 
                    page_url='https://pet2cattle.com',
                    pagination_prefix='/search/',
                    page_number=page,
                    # has_next=response['next'],
                    has_next=False,
                    has_previous=page>0,
                    navigation=get_navigation(),
                    tag_cloud=get_tag_cloud(),
                    search_enabled=search_enabled
                  )

@app.route('/static/<file_category>/<filename>')
@cache.cached(timeout=86400)
def static_files(file_category, filename):
  if DEBUG:
    print('static')
  try:
    if DEBUG:
      print('url: static/'+file_category+'/'+filename)
    response = make_response(models.Static(file_category+'/'+filename, None, None).get_data().read(), 200)
    if filename.endswith('.jpg'):
      response.mimetype = "image/jpeg"
    elif filename.endswith('.jpeg'):
      response.mimetype = "image/jpeg"
    elif filename.endswith('.png'):
      response.mimetype = "image/png"
    else:
      response.mimetype = "image/jpeg"
    return response
  except Exception as e:
    if DEBUG:
      print(str(e))
    abort(404)

@app.route('/sitemap<sitemap_name>')
@app.route('/feed<sitemap_name>')
@cache.cached(timeout=86400)
def sitemap(sitemap_name):
  if DEBUG:
    print('sitemap')
  try:
    response = make_response(models.Sitemap('sitemap'+sitemap_name, None, None).get_data().read(), 200)
    if sitemap_name.endswith('.rss'):
      response.mimetype = "application/rss+xml"
    elif sitemap_name.endswith('.gz'):
      response.mimetype = "application/x-gzip"
    else:
      response.mimetype = "application/xml"
    return response
  except:
    abort(404)

@app.route('/favicon.ico')
def favicon():
  if DEBUG:
    print('favicon')
  try:
    response = make_response(models.S3File('', 'favicon.ico').get_data().read(), 200)
    response.mimetype = "image/x-icon"
    return response
  except Exception as e:
    if DEBUG:
      print(str(e))
    abort(404)

@app.route('/robots.txt')
def robots():
  if DEBUG:
    print('robots')
  lines = [
    "User-Agent: *",
    "Allow: /",
    "",
    "Sitemap: http://pet2cattle.com/sitemap.xml",
    ""
  ]
  response = make_response("\n".join(lines), 200)
  response.mimetype = "text/plain"
  return response

@cache.cached(timeout=7200, key_prefix="get_tags")
def get_posts_tags():
  try:
    return pickle.loads(models.S3File('indexes', 'tags.dict').get_data().read())
  except Exception as e:
    if DEBUG:
      print(str(e))
    return None

@app.route('/tags', defaults={'tag': None, 'page': 0})
@app.route('/tags/<tag>', defaults={'page': 0})
@app.route('/tags/<tag>/', defaults={'page': 0})
@app.route('/tags/<tag>/page/<int:page>')
@cache.cached(timeout=7200)
def tags(tag, page):
  if DEBUG:
    print('tags')
  tags = get_posts_tags()

  if not tags:
    abort(404)

  if page == 0:
    tag_canonical_url = CANONICAL_DOMAIN+'/tags/'+tag+'/'
  else:
    tag_canonical_url = CANONICAL_DOMAIN+'/tags/'+tag+'/page/'+str(page)

  if tag:
    if tag in tags.keys():
      page_metadata={}
      page_metadata['robots']='noindex,follow'
      page_metadata['title']=['Tag: '+tag]
      page_metadata['keywords']=[tag]
      page_metadata['summary']=['Post containing '+tag+' tag']

      prefix='/tags/'+tag

      posts_urls = tags[tag][page*5:page*5+5]

      if not posts_urls:
        abort(404)

      posts = []
      for post_url in posts_urls:
        candidate = models.Post.getURL(post_url)
        if candidate:
          posts.append(candidate[0])

      return render_template('index.html', 
                        single=False,
                        posts=posts, 
                        post_metadata=page_metadata, 
                        page_url='https://pet2cattle.com',
                        canonical_url=tag_canonical_url,
                        pagination_prefix=prefix+'/',
                        page_number=page,
                        has_next=tags[tag][(page+1)*10:(page+1)*10+10],
                        has_previous=page>0,
                        navigation=get_navigation(),
                        tag_cloud=None,
                        search_enabled=search_enabled
                      )
    else:
      abort(404)
  else:
    # TODO: llista de tags
    abort(404)

@cache.cached(timeout=7200, key_prefix="get_categories")
def get_posts_categories():
  try:
    return pickle.loads(models.S3File('indexes', 'categories.dict').get_data().read())
  except Exception as e:
    if DEBUG:
      print(str(e))
    return None

@cache.cached(timeout=7200, key_prefix="get_cat2tag")
def get_cat2tag():
  try:
    return pickle.loads(models.S3File('indexes', 'cat2tag.dict').get_data().read())
  except Exception as e:
    if DEBUG:
      print(str(e))
    return None

@app.route('/categories', defaults={'category': None, 'page': 0})
@app.route('/categories/<category>', defaults={'page': 0})
@app.route('/categories/<category>/', defaults={'page': 0})
@app.route('/categories/<category>/page/<int:page>')
@cache.cached(timeout=7200)
def categories(category, page):
  if DEBUG:
    print('categories')
  categories = get_posts_categories()
  cat2tag = get_cat2tag()

  if DEBUG:
    print("CATEGORIES")
    print(str(categories))
    print("CAT2TAG")
    print(str(cat2tag))

  if not categories:
    abort(404)

  if page == 0:
    category_canonical_url = CANONICAL_DOMAIN+'/categories/'+category+'/'
  else:
    category_canonical_url = CANONICAL_DOMAIN+'/categories/'+category+'/page/'+str(page)

  if category:
    if category in categories.keys():
      page_metadata={}
      page_metadata['robots']='noindex,follow'
      page_metadata['title']=['Categories: '+category]
      page_metadata['keywords']=[category]
      page_metadata['summary']=['Posts belonging to the '+category+' category']

      prefix='/categories/'+category

      posts_urls = categories[category][page*5:page*5+5]

      related_categories = []
      other_related_categories = []

      get_key_value = lambda obj: obj['weight']
      for related_cat in sorted(get_related_categories(category), key=get_key_value, reverse=True)[:3]:
        related_categories.append(related_cat)

      for related_cat in sorted(get_related_categories(category), key=get_key_value, reverse=False)[:3]:
        if related_cat not in related_categories:
          other_related_categories.append(related_cat)

      if not posts_urls:
        abort(404)

      posts = []
      for post_url in posts_urls:
        candidate = models.Post.getURL(post_url)
        if candidate:
          posts.append(candidate[0])

      return render_template('index.html', 
                        single=False,
                        posts=posts, 
                        post_metadata=page_metadata, 
                        page_url='https://pet2cattle.com',
                        canonical_url=category_canonical_url,
                        pagination_prefix=prefix+'/',
                        page_number=page,
                        has_next=categories[category][(page+1)*10:(page+1)*10+10],
                        has_previous=page>0,
                        principal_related_posts=related_categories,
                        other_related_posts=other_related_categories,
                        navigation=get_navigation(),
                        tag_cloud=None,
                        cat2tag=cat2tag[category],
                        search_enabled=search_enabled
                      )
    else:
      abort(404)
  else:
    # TODO: llista de categories
    abort(404)

@app.route('/<int:year>/page/<int:page>', defaults={'month': None})
@app.route('/<int:year>/', defaults={'month': None, 'page': 0})
@app.route('/<int:year>/<month>/page/<int:page>')
@app.route('/<int:year>/<month>/', defaults={'page': 0})
@cache.cached(timeout=86400)
def archives(year, month, page):
  if DEBUG:
    print('RESPONSE archives')
  page_metadata={}
  page_metadata['robots']='noindex,follow'
  
  archive_canonical_url = CANONICAL_DOMAIN+'/'+str(year)+'/'
  if month:
    archive_canonical_url += month+'/'
  if page != 0:
    archive_canonical_url += 'page/'+str(page)

  page_metadata['keywords']=['terraform, kubernetes, helm, pet vs cattle']
  if month:
    try:
      month_name = datetime.date(1900, int(month), 1).strftime('%B')
      page_metadata['title']=['Archives '+month_name+' '+str(year)]
      page_metadata['summary']=['List of posts published on '+month_name+' '+str(year)]
    except Exception as e:
      print(str(e))
      abort(404)
  else:
    page_metadata['title']=['Archives for year: '+str(year)]
    page_metadata['summary']=['List of posts published on year '+str(year)]

  if month:
    limit = 10
    prefix = '/'+str(year)+'/'+re.sub(r'[^0-9]', '', month)
  else:
    prefix = '/'+str(year)
    limit = 15

  response = models.Post.all(page=page, limit=limit, prefix=prefix)

  if len(response['Posts'])==0:
    print('empty')
    abort(404)

  return render_template('index.html', 
                    single=False,
                    posts=response['Posts'], 
                    post_metadata=page_metadata, 
                    page_url='https://pet2cattle.com',
                    canonical_url=archive_canonical_url,
                    pagination_prefix=prefix+'/',
                    page_number=page,
                    has_next=response['next'],
                    has_previous=page>0,
                    navigation=get_navigation(),
                    tag_cloud=None,
                    search_enabled=search_enabled
                  )

@app.route('/<int:year>/<month>/<slug>')
@cache.cached(timeout=7200)
def post(year, month, slug):
  if DEBUG:
    print('post')
  try:
    post = models.Post.filter(str(year), re.sub(r'[^0-9]', '', month), slug)[0]
    if post.is_published() or FORCE_PUBLISH:
      return render_template('post.html',
                        single=True, 
                        post_html=post.html, 
                        post_metadata=post.metadata, 
                        page_url=post.url,
                        canonical_url=CANONICAL_DOMAIN+post.url,
                        keywords=post.get_keywords(),
                        categories=post.get_categories(),
                        tags=post.get_tags(),
                        navigation=get_navigation(),
                        search_enabled=search_enabled
                  )
  except:
    pass
  return catch_all(str(year)+'/'+month+'/'+slug)

@cache.cached(timeout=43200, key_prefix="get_tag_cloud")
def get_tag_cloud():
  try:
    return pickle.loads(models.S3File('indexes', 'tag_cloud.dict').get_data().read())
  except Exception as e:
    if DEBUG:
      print(str(e))
    return None

@app.route('/', defaults={'page': 0})
@app.route('/page/<int:page>')
@cache.cached(timeout=7200)
def index(page):
  if DEBUG:
    print('RESPONSE index')
  page_metadata={}
  page_metadata['title']=['From pet to cattle']
  if page!=0:
    page_metadata['robots']='noindex,follow'
  page_metadata['keywords']=['kubernetes, helm, terraform, pet vs cattle']
  page_metadata['summary']=['Treat your clusters like cattle, not pets by using kubernetes, helm and terraform']

  try:
    webindex = get_webindex_page()[page]
  except:
    if DEBUG:
      print('error webindex')
    abort(404)

  if webindex:
    try:
      response = { 'Posts': [] }

      for post_url in webindex:
        split_url = post_url.split('/')

        response['Posts'].append(models.Post.filter(split_url[1], split_url[2], split_url[3])[0])

        response['next']=page+1 in get_webindex_page().keys()
        response['page']=page
    except Exception as e:
      if DEBUG:
        print("exception: "+str(e))
      abort(503)
    if DEBUG:
      print("using webindex")
  else:
    if DEBUG:
      print('error webindex')
    abort(404)  


  if len(response['Posts'])==0:
    if DEBUG:
      print('empty')
    abort(404)

  # print("ARCHIVES: "+str(get_archives()))

  return render_template('index.html', 
                    single=False,
                    archives=get_archives(),
                    posts=response['Posts'], 
                    post_metadata=page_metadata, 
                    page_url='https://pet2cattle.com',
                    pagination_prefix='/',
                    page_number=page,
                    has_next=response['next'],
                    has_previous=page>0,
                    navigation=get_navigation(),
                    tag_cloud=get_tag_cloud(),
                    search_enabled=search_enabled
                  )

@app.route('/<path:path>')
@cache.cached(timeout=86400)
def catch_all(path):
  if DEBUG:
    print("RESPONSE catchall")
  try:
    if DEBUG:
      print('/'+path)
    page = models.Page.filter('/'+path)[0]
    if page.is_published() or FORCE_PUBLISH:
      if DEBUG:
        print('is page')
      
      # generate dynamic content
      page.autopage()
      return render_template('page.html',
                        single=True, 
                        post_html=page.html, 
                        post_metadata=page.metadata, 
                        page_url=page.url,
                        canonical_url=CANONICAL_DOMAIN+page.url,
                        keywords=page.get_keywords(),
                        navigation=get_navigation(),
                        search_enabled=search_enabled
                  )
    else:
      if DEBUG:
        print(page.url+' is not published')
  except Exception as e:
    if DEBUG:
      print(str(e))

  try:
    redirects_302 = cache.get('redirects_302')
    if not redirects_302:
      redirects_302 = yaml.safe_load(models.S3File('redirects', '302.yaml').get_data())
    try:
      if DEBUG:
        print('redirect 302')
      return redirect(redirects_302['redirect']['/'+path], code=302)
    except:
      pass

  except Exception as e:
    if DEBUG:
      print(str(e))
    pass
  abort(404)