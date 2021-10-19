import app.models

import requests
import time

# Posts

while True:
  try:
    posts = app.models.Post.all(page=0, limit=-1)['Posts']
    posts.reverse()

    for post in posts:
      print("==="+post.url)
      try:
        requests.get("http://localhost:8000"+post.url)
      except Exception as e:
        print(str(e))
      time.sleep(15)
    
    time.sleep(600)
  except Exception as e:
    print(str(e))
    time.sleep(60)