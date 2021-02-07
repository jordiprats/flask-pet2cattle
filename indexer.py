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

try:
    tag_cloud = {}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for tag in post.get_tags():
            tag_cloud[tag] = { 'count': len(tags[slugify(tag)]), 'url': '/tags/'+slugify(tag)}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for category in post.get_categories():
            tag_cloud[category] = { 'count': len(categories[slugify(category)]), 'url': '/categories/'+slugify(category)}

    tmp_tagcloud = tempfile.TemporaryFile()

    pickle.dump(tags, tmp_tagcloud)
    tmp_tagcloud.seek(os.SEEK_SET)

    tagcloud_idx = app.models.S3File('indexes', 'tag_cloud.dict')
    tagcloud_idx.save(tmp_tagcloud)

    print("tag_cloud.dict OK")
    print(str(tag_cloud))
except Exception as e:
    print("Error generant tag_cloud.dict: "+str(e))