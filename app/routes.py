from flaskext.markdown import Markdown
from flask import send_from_directory
from flask import render_template
from app import app

import markdown
import os

md = Markdown(app,
              extensions=['meta'],
              safe_mode=True,
              output_format='html4',
             )

@app.route('/')
def index():
    try:
        llista = ''
        for path, dirnames, filenames in sorted(os.walk('app/posts')):
            for filename in filenames:
                md_file = os.path.join(path, filename)
                with open(md_file, 'r') as reader:
                    md_data = reader.read()

                    md = markdown.Markdown(extensions=['markdown.extensions.fenced_code', 'markdown.extensions.meta'])
                    post_html = md.convert(md_data)
                    post_metadata = md.Meta
    except Exception as e:
        print(str(e))

    return render_template('base.html', post_html=post_html, post_metadata=post_metadata)
