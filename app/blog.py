
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
import re
import os

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

@app.route('/robots.txt')
@cache.cached(timeout=3600)
def robots():
    lines = [
        "User-Agent: *",
        "Disallow: /wp-admin/",
    ]
    response = make_response("\n".join(lines), 200)
    response.mimetype = "text/plain"
    return response

@app.route('/<year>/<month>/<slug>')
@cache.cached(timeout=3600)
def post(year, month, slug):
    try:
        post = models.Post.filter(re.sub(r'[^0-9]', '', year), re.sub(r'[^0-9]', '', month), slug)[0]
        if post.is_published():
            return render_template('post.html',
                                                single=True, 
                                                post_html=post.html, 
                                                post_metadata=post.metadata, 
                                                page_url=post.url, 
                                                keywords=post.get_keywords()
                                    )
    except:
        pass
    abort(404)

@app.route('/about')
def about():
    return redirect('https://github.com/jordiprats', code=302)

@app.route('/', defaults={'page': 0})
@app.route('/page/<page>')
@cache.cached(timeout=3600)
def index(page):
    page_metadata={}
    page_metadata['title']=['From pet to cattle']
    page_metadata['keywords']=['k8s, terraform, kubernetes, pet vs cattle']

    response = models.Post.all(int(page), 5)

    if len(response['Posts'])==0:
        abort(404)

    return render_template('index.html', 
                                        single=False,
                                        posts=response['Posts'], 
                                        post_metadata=page_metadata, 
                                        page_url='https://pet2cattle.com',
                                        page_number=response['page'],
                                        has_next=response['next'],
                                        has_previous=response['page']>0,
                                    )

@app.route('/<path:path>')
def catch_all(path):
    abort(404)