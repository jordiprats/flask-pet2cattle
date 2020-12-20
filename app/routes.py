from flaskext.markdown import Markdown
from flask import send_from_directory
from flask import render_template
from flask import redirect
from flask import abort

from slugify import slugify

from app import app

import markdown
import re
import os


md = Markdown(app,
              extensions=['meta'],
              safe_mode=True,
              output_format='html4',
             )

@app.route('/<any>/<mes>/<slug>')
def post(any, mes, slug):
    print('post')
    for path, dirnames, filenames in sorted(os.walk(os.path.join('app', 'posts', any, mes))):
        for filename in filenames:
            filename_slug = slugify(re.sub('^[0-9]+ ', '', filename))

            if slug==filename_slug:
                md_file = os.path.join(path, filename)
                with open(md_file, 'r') as reader:
                    md_data = reader.read()

                    md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
                    post_html = md.convert(md_data)
                    post_metadata = md.Meta
                    page_url = '/'+any+'/'+mes+'/'+filename_slug
                    return render_template('post.html', post_html=post_html, post_metadata=post_metadata, page_url=page_url)

    abort(404)

@app.route('/about')
def about():    
    return redirect('https://github.com/jordiprats', code=302)

@app.route('/')
def index():
    post_metadata={}
    post_metadata['title']=['From pet to cattle']
    post_metadata['keywords']=['k8s, terraform, kubernetes, pet vs cattle']
    posts = []
    for path, dirnames, filenames in sorted(os.walk('app/posts')):
        for filename in filenames:
            md_file = os.path.join(path, filename)
            filename_slug = slugify(re.sub('^[0-9]+ ', '', filename))
            with open(md_file, 'r') as reader:
                post = {}
                lines = reader.readlines(2000)

                excerpt = ''
                for line in lines:
                    if line == '<!-- more -->\n':
                        break
                    excerpt += line

                md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
                excerpt_html = md.convert(excerpt)
                post['url'] = re.sub('app/posts', '', path)+'/'+filename_slug
                post['meta'] = md.Meta
                post['excerpt'] = re.sub('<h1>.*</h1>', '', excerpt_html)

                posts.append(post)

    return render_template('index.html', posts=posts, post_metadata=post_metadata, page_url='https://pet2cattle.com')
