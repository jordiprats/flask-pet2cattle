from slugify import slugify

import app.models

import tempfile
import pickle
import os

try:
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

    print("categories.dict OK")
except Exception as e:
    print("Error generant categories.dict: "+str(e))

try:
    tags = {}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for tag in post.get_tags():
            if slugify(tag) in tags.keys():
                tags[slugify(tag)].append(post.url)
            else:
                tags[slugify(tag)]=[post.url]

    tmp_tags = tempfile.TemporaryFile()

    pickle.dump(tags, tmp_tags)
    tmp_tags.seek(os.SEEK_SET)

    tags_idx = app.models.S3File('indexes', 'tags.dict')
    tags_idx.save(tmp_tags)

    print("tags.dict OK")
except Exception as e:
    print("Error generant tags.dict: "+str(e))