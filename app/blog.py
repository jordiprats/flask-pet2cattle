
from flaskext.markdown import Markdown
from flask_caching import Cache

from flask import send_from_directory
from flask import render_template
from flask import make_response
from flask import redirect
from flask import abort

from datetime import datetime
from slugify import slugify

from app import models
from app import app

import markdown
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


config = {
    "DEBUG": False,          # some Flask specific configs
    "CACHE_TYPE": "filesystem", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
    'CACHE_DIR': 'cache'
}

app.config.from_mapping(config)
cache = Cache(app)
cache.clear()

md = Markdown(app,
              extensions=['meta'],
              safe_mode=True,
              output_format='html4',
             )

@cache.cached(timeout=86400, key_prefix="get_navigation")
def get_navigation():
    page_urls = models.Page.urls()

    nav = []

    for page_url in page_urls:
        print('/'+page_url)
        print(str(models.Page.filter('/'+page_url)))
        if '/' in page_url:
            # TODO: multiples subpagines?
            nav.append([page_url.split('/'), models.Page.filter('/'+page_url)[0].get_title()])
        else:
            nav.append([page_url, models.Page.filter('/'+page_url)[0].get_title()])

    return nav

@app.route('/sitemap<sitemap_name>')
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
    except:
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

@app.route('/<int:year>/page/<int:page>', defaults={'month': None})
@app.route('/<int:year>/', defaults={'month': None, 'page': 0})
@app.route('/<int:year>/<month>/page/<int:page>')
@app.route('/<int:year>/<month>/', defaults={'page': 0})
@cache.cached(timeout=86400)
def archives(year, month, page):
    if DEBUG:
        print('archives')
    page_metadata={}
    page_metadata['robots']='noindex,follow'
    page_metadata['title']=['Archives: From pet to cattle']
    page_metadata['keywords']=['terraform, kubernetes, helm, pet vs cattle']

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
                                        pagination_prefix=prefix+'/',
                                        page_number=page,
                                        has_next=response['next'],
                                        has_previous=page>0,
                                        navigation=get_navigation()
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
                                                keywords=post.get_keywords(),
                                                navigation=get_navigation()
                                    )
    except:
        pass
    return catch_all(str(int)+'/'+month+'/'+slug)

@app.route('/', defaults={'page': 0})
@app.route('/page/<int:page>')
@cache.cached(timeout=7200)
def index(page):
    if DEBUG:
        print('index')
    page_metadata={}
    page_metadata['title']=['From pet to cattle']
    if page!=0:
        page_metadata['robots']='noindex,follow'
    page_metadata['keywords']=['kubernetes, helm, terraform, pet vs cattle']
    page_metadata['summary']=['Treat your clusters like cattle, not pets by learning how to use kubernetes, helm and terraform']

    response = models.Post.all(page, 5)

    if len(response['Posts'])==0:
        print('empty')
        abort(404)

    return render_template('index.html', 
                                        single=False,
                                        posts=response['Posts'], 
                                        post_metadata=page_metadata, 
                                        page_url='https://pet2cattle.com',
                                        pagination_prefix='/',
                                        page_number=page,
                                        has_next=response['next'],
                                        has_previous=page>0,
                                        navigation=get_navigation()
                                    )

@app.route('/<path:path>')
@cache.cached(timeout=86400)
def catch_all(path):
    print(str(get_navigation()))
    try:
        if DEBUG:
            print('/'+path)
        page = models.Page.filter('/'+path)[0]
        if page.is_published() or FORCE_PUBLISH:
            if DEBUG:
                print('is page')
            return render_template('page.html',
                                                single=True, 
                                                post_html=page.html, 
                                                post_metadata=page.metadata, 
                                                page_url=page.url, 
                                                keywords=page.get_keywords(),
                                                navigation=get_navigation()
                                    )
        else:
            if DEBUG:
                print(page.url+' is not published')
    except Exception as e:
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
        print(str(e))
        pass
    abort(404)