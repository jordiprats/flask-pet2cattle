from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

import app.models

import requests
import time

def is_valid(url):
  parsed = urlparse(url)
  return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url):
  urls = set()

  domain_name = urlparse(url).netloc
  soup = BeautifulSoup(requests.get(url).content, "html.parser")

  for a_tag in soup.findAll("a"):
    href = a_tag.attrs.get("href")
    if not href:
        continue

    href = urljoin(url, href)

    parsed_href = urlparse(href)
    href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

    if not is_valid(href):
        continue
    if domain_name not in href:
        continue
    urls.add(href)
  return urls

# Posts

while True:
  try:
    # fetch homepage tags
    for url in get_all_website_links('http://127.0.0.1:8000/'):
      print("==="+url)
      try:
        requests.get(url)
      except Exception as e:
        print(str(e))
      time.sleep(5)

    # refresh posts
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