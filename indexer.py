from whoosh.filedb.filestore import FileStorage
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, ID, TEXT

from slugify import slugify
from whoosh import index

import app.models

import tempfile
import datetime
import random
import pickle
import sys
import os

FULLTEXT_INDEX_PATH = os.getenv('FULLTEXT_INDEX_PATH', "whoosh")

def getFTschema():
  return Schema(
                path=ID(stored=True,unique=True), 
                content=TEXT(analyzer=StemmingAnalyzer()), 
                title=TEXT(analyzer=StemmingAnalyzer()), 
                keywords=TEXT
              )

if __name__ == "__main__":

  posts = app.models.Post.all(page=0, limit=-1)['Posts']

  try:
    categories = {}

    for post in posts:
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

    for post in posts:
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

    for post in posts:
      for tag in post.get_tags():
        ordered_tag_cloud[tag] = { 'count': len(tags[slugify(tag)]), 'url': '/tags/'+slugify(tag)}

    for post in posts:
      for category in post.get_categories():
        ordered_tag_cloud[category] = { 'count': len(categories[slugify(category)]), 'url': '/categories/'+slugify(category)}

    count = 0
    sum = 0
    to_delete = []
    tag_keys = list(ordered_tag_cloud.keys())
    random.shuffle(tag_keys)
    for tag in tag_keys:
      if ordered_tag_cloud[tag]['count']>3:
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

    for post in posts:
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
    
  try:
    cat2relatedcats = {}

    for post in posts:
      for category in post.get_categories():
        if slugify(category) not in cat2relatedcats.keys():
          cat2relatedcats[slugify(category)] = {}
        for related_cat in post.get_categories():
          if category != related_cat:
            if slugify(related_cat) not in cat2relatedcats[slugify(category)].keys():
              cat2relatedcats[slugify(category)][slugify(related_cat)] = { 'title': related_cat, 'weight': 1, 'url': '/categories/'+slugify(related_cat)}
            else:
              cat2relatedcats[slugify(category)][slugify(related_cat)]['weight'] += 1
            # cat2relatedcats[category].append(related_cat)

    tmp_c2rc = tempfile.TemporaryFile()

    pickle.dump(cat2relatedcats, tmp_c2rc)
    tmp_c2rc.seek(os.SEEK_SET)

    c2rc_idx = app.models.S3File('indexes', 'cat2relatedcats.dict')
    c2rc_idx.save(tmp_c2rc)

    print("cat2relatedcats.dict OK")
    
  except Exception as e:
    print("Error generant cat2relatedcats.dict: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

  try:
    autopage = {}

    for post in posts:
      for autopage_instance in post.get_autopages():     
        if autopage_instance not in autopage.keys():
          autopage[autopage_instance] = {}

        autopage_category = post.get_metadata('autopage_category')

        if not autopage_category:
          autopage_category = 'unsorted'

        if autopage_category not in autopage[autopage_instance].keys():
          autopage[autopage_instance][autopage_category] = []

        autopage_post = { 'url': post.get_url() }

        if post.get_metadata('autopage_title'):
          autopage_post['title'] = post.get_metadata('autopage_title')
        else:
          autopage_post['title'] = post.get_short_title()

        if post.get_metadata('autopage_description'):
          autopage_post['description'] = post.get_metadata('autopage_description')
        else:
          autopage_post['description'] = post.get_metadata('summary')

        autopage[autopage_instance][autopage_category].append(autopage_post)

    # print(str(autopage))

    tmp_autopage = tempfile.TemporaryFile()

    pickle.dump(autopage, tmp_autopage)
    tmp_autopage.seek(os.SEEK_SET)

    autopage_idx = app.models.S3File('indexes', 'autopage.dict')
    autopage_idx.save(tmp_autopage)

    print("autopage_idx.dict OK")

  except Exception as e:
    print("Error generant autopage_idx.dict: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

  #
  # full text search
  #

  try:
    if not os.path.exists(FULLTEXT_INDEX_PATH):
        os.makedirs(FULLTEXT_INDEX_PATH, exist_ok=True)

    idx_storage = FileStorage(FULLTEXT_INDEX_PATH)

    if not index.exists_in(FULLTEXT_INDEX_PATH):
      print('creating new whoosh index')
      schema = getFTschema()
      idx = index.create_in(FULLTEXT_INDEX_PATH, schema)
    else:
      idx = idx_storage.open_index()

    idx_writer = idx.writer()

    for post in posts:
      keywords = " ".join(post.get_categories())+' '+" ".join(post.get_keywords())+' '+" ".join(post.get_tags())
      # print(keywords)
      idx_writer.update_document(
                                  path=post.get_url(), 
                                  content=post.get_raw_md().lower(), 
                                  title=post.get_title().lower(),
                                  keywords=keywords, 
                                )

    # TODO: altres pagines a indexar? per exemple CKA

    idx_writer.commit()

    print("full text search index (whoosh) OK")

  except Exception as e:
    print("Error generant full text search index: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

  #
  # archives
  #

  try:
    archives = {}
    
    for post in posts:
      url = post.get_url()
      url_components = url.split('/')

      title = datetime.date(1900, int(url_components[2]), 1).strftime('%B')+" "+url_components[1]

      if title not in archives.keys():
        archives[title]="/".join(url_components[0:3])

    # print(str(archives))

    tmp_archives = tempfile.TemporaryFile()

    pickle.dump(archives, tmp_archives)
    tmp_archives.seek(os.SEEK_SET)

    archives_dict = app.models.S3File('indexes', 'archives.dict')
    archives_dict.save(tmp_archives)

    print("archives.dict OK")

  except Exception as e:
    print("Error generant archive list: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

  #
  # web index
  #

  try:
    webindex = {}

    page_num = 0
    post_count = 0

    for post in posts:
      if post_count >= 5:
        page_num+=1
        post_count=0
      
      if page_num in webindex.keys():
        webindex[page_num].append(post.get_url())
      else:
        webindex[page_num]=[post.get_url()]
      
      post_count+=1
    
    # print(str(webindex))

    tmp_webindex = tempfile.TemporaryFile()

    pickle.dump(webindex, tmp_webindex)
    tmp_webindex.seek(os.SEEK_SET)

    webindex_dict = app.models.S3File('indexes', 'webindex.dict')
    webindex_dict.save(tmp_webindex)

    print("webindex.dict OK")

  except Exception as e:
    print("Error generant page_index: "+str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
