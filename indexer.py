from slugify import slugify

import app.models

import tempfile
import random
import pickle
import sys
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
    ordered_tag_cloud = {}
    tag_cloud = {}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for tag in post.get_tags():
            ordered_tag_cloud[tag] = { 'count': len(tags[slugify(tag)]), 'url': '/tags/'+slugify(tag)}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for category in post.get_categories():
            ordered_tag_cloud[category] = { 'count': len(categories[slugify(category)]), 'url': '/categories/'+slugify(category)}

    count = 0
    sum = 0
    to_delete = []
    tag_keys = list(ordered_tag_cloud.keys())
    random.shuffle(tag_keys)
    for tag in tag_keys:
        if ordered_tag_cloud[tag]['count']!=1:
            tag_cloud[tag] = ordered_tag_cloud[tag]
            count += 1
            sum += tag_cloud[tag]['count']
    
    mean = sum/count
    # print(mean)

    for tag in tag_cloud.keys():
        if tag_cloud[tag]['count'] > mean+(mean/2):
            tag_cloud[tag]['size'] = "h2"
        elif tag_cloud[tag]['count'] > mean:
            tag_cloud[tag]['size'] = "h3"
        elif tag_cloud[tag]['count'] > mean-(mean/2):
            tag_cloud[tag]['size'] = "h5"
        else:
            tag_cloud[tag]['size'] = "h6"

    tmp_tagcloud = tempfile.TemporaryFile()

    pickle.dump(tag_cloud, tmp_tagcloud)
    tmp_tagcloud.seek(os.SEEK_SET)

    tagcloud_idx = app.models.S3File('indexes', 'tag_cloud.dict')
    tagcloud_idx.save(tmp_tagcloud)

    print("tag_cloud.dict OK")
except Exception as e:
    print("Error generant tag_cloud.dict: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

try:
    cat2tag = {}

    for post in app.models.Post.all(page=0, limit=-1)['Posts']:
        for category in post.get_categories():
            if slugify(category) in cat2tag.keys():
                tags = cat2tag[slugify(category)]
            else:
                tags = {}
            for tag in post.get_tags():
                if tag in tags.keys():
                    tags[tag] = { 'count': tags[tag]['count']+1, 'url': '/tags/'+slugify(tag)}
                else:
                    tags[tag] = { 'count': 1, 'url': '/tags/'+slugify(tag)}
            cat2tag[slugify(category)] = tags

            count = 0
            sum = 0
            for tag in cat2tag[slugify(category)].keys():
                count += 1
                sum += cat2tag[slugify(category)][tag]['count']
            
            mean = sum/count

            for tag in cat2tag[slugify(category)].keys():
                if cat2tag[slugify(category)][tag]['count'] > mean+(mean/2):
                    cat2tag[slugify(category)][tag]['size'] = "h2"
                elif cat2tag[slugify(category)][tag]['count'] > mean:
                    cat2tag[slugify(category)][tag]['size'] = "h3"
                elif cat2tag[slugify(category)][tag]['count'] > mean-(mean/2):
                    cat2tag[slugify(category)][tag]['size'] = "h5"
                else:
                    cat2tag[slugify(category)][tag]['size'] = "h6"

    tmp_c2t = tempfile.TemporaryFile()

    pickle.dump(cat2tag, tmp_c2t)
    tmp_c2t.seek(os.SEEK_SET)

    c2t_idx = app.models.S3File('indexes', 'cat2tag.dict')
    c2t_idx.save(tmp_c2t)

    print("cat2tag.dict OK")
except Exception as e:
    print("Error generant cat2tag.dict: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

