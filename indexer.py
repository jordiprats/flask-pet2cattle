from slugify import slugify

import app.models

import tempfile
import pickle
import os

categories = {}

for post in app.models.Post.all(page=0, limit=-1)['Posts']:
    for category in post.get_categories():
        if slugify(category) in categories.keys():
            categories[slugify(category)].append(post.url)
        else:
            categories[slugify(category)]=[post.url]

tmp_categories = tempfile.TemporaryFile()

pickle.dump(categories, tmp_categories)
tmp_categories.seek(os.SEEK_SET)

categories_idx = app.models.S3File('indexes', 'categories.dict')
categories_idx.save(tmp_categories)
