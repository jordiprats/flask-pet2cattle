import app.models

import requests
import time

# Posts

while True:
  posts = app.models.Post.all(page=0, limit=-1)['Posts']
  posts.reverse()

  for post in posts:
    print("==="+post.url)
    requests.get("https://pet2cattle.com"+post.url)
    time.sleep(30)
  
  time.sleep(600)