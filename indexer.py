# import app.models

# import tempfile
# import pickle
# import os

# categories = {}

# for post in app.models.Post.all(page=0, limit=-1)['Posts']:
#     for category in post.get_categories():
#         if category in categories.keys():
#             categories[category].append(post.url)
#         else:
#             categories[category]=[post.url]

# tmp_categories = tempfile.TemporaryFile()

# pickle.dump(categories, tmp_categories)
# tmp_categories.seek(os.SEEK_SET)

# categories_idx = app.models.S3File('indexes', 'categories.dict')
# categories_idx.save(tmp_categories)
