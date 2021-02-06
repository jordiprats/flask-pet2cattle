from slugify import slugify
from .. import app

@app.template_filter('slugify')
def slugify_text(text):
    """slugify a given text"""
    return slugify(text)
