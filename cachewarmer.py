from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

import requests
import sys

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

try:
  website = sys.argv[1]
except:
  website = 'https://pet2cattle.com'

for url in get_all_website_links(website):
  print(url)
  requests.get(url)