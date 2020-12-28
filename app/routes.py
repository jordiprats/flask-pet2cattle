from flaskext.markdown import Markdown
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

md = Markdown(app,
              extensions=['meta'],
              safe_mode=True,
              output_format='html4',
             )

@app.route('/robots.txt')
def robots():
    lines = [
        "User-Agent: *",
        "Disallow: /wp-admin/",
    ]
    response = make_response("\n".join(lines), 200)
    response.mimetype = "text/plain"
    return response

@app.route('/<year>/<mes>/<slug>')
def post(year, mes, slug):
    try:
        post = models.Post.filter(year, mes, slug)[0]
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
def index(page):
    page_metadata={}
    page_metadata['title']=['From pet to cattle']
    page_metadata['keywords']=['k8s, terraform, kubernetes, pet vs cattle']

    posts = models.Post.all(int(page), 5)

    if len(posts)==0:
        abort(404)

    print(str(posts))
    return render_template('index.html', single=False, posts=posts, post_metadata=page_metadata, page_url='https://pet2cattle.com')

@app.route('/<path:path>')
def catch_all(path):
    abort(404)