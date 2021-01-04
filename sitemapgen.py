from datetime import datetime

import app.models

import tempfile
import gzip
import os

tmp_sitemap_pages = tempfile.TemporaryFile()
with gzip.open(filename=tmp_sitemap_pages, mode='wb') as sitemap_pages:
    sitemap_pages.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
    sitemap_pages.write(bytes('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n', 'utf-8'))

    sitemap_pages.write(bytes('\t<url>\n', 'utf-8'))
    sitemap_pages.write(bytes('\t\t<loc>https://pet2cattle.com/</loc>\n', 'utf-8'))
    sitemap_pages.write(bytes('\t\t<lastmod>'+datetime.now().strftime("%Y-%m-%d")+'</lastmod>\n', 'utf-8'))
    sitemap_pages.write(bytes('\t\t<changefreq>daily</changefreq>\n', 'utf-8'))
    sitemap_pages.write(bytes('\t\t<priority>0.6</priority>\n', 'utf-8'))
    sitemap_pages.write(bytes('\t</url>\n', 'utf-8'))

    sitemap_pages.write(bytes('</urlset>', 'utf-8'))

tmp_sitemap_pages.seek(os.SEEK_SET)

sm_pages = app.models.Sitemap('sitemap-pages.xml.gz', datetime.now(), tmp_sitemap_pages)
sm_pages.save()
tmp_sitemap_pages.close()

tmp_sitemap_posts = tempfile.TemporaryFile()
with gzip.open(filename=tmp_sitemap_posts, mode='wb') as sitemap_posts:
    sitemap_posts.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
    sitemap_posts.write(bytes('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n', 'utf-8'))
    posts = app.models.Post.all(page=0, limit=-1)['Posts']
    print(str(posts))
    for post in posts:
        print(str(post))
        sitemap_posts.write(bytes('\t<url>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<loc>https://pet2cattle.com'+post.url+'</loc>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<lastmod>'+post.get_last_modified().strftime("%Y-%m-%d")+'</lastmod>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<changefreq>monthly</changefreq>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<priority>0.5</priority>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t</url>\n', 'utf-8'))
    sitemap_posts.write(bytes('</urlset>', 'utf-8'))

tmp_sitemap_posts.seek(os.SEEK_SET)

sm_posts = app.models.Sitemap('sitemap-posts.xml.gz', datetime.now(), tmp_sitemap_posts)
sm_posts.save()
tmp_sitemap_posts.close()

sitemap_base = tempfile.TemporaryFile()
sitemap_base.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
sitemap_base.write(bytes('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n', 'utf-8'))

sitemap_base.write(bytes('\t<sitemap>\n', 'utf-8'))
sitemap_base.write(bytes('\t\t<loc>https://pet2cattle.com/sitemap-pages.xml.gz</loc>\n', 'utf-8'))
sitemap_base.write(bytes('\t</sitemap>\n', 'utf-8'))

sitemap_base.write(bytes('\t<sitemap>\n', 'utf-8'))
sitemap_base.write(bytes('\t\t<loc>https://pet2cattle.com/sitemap-posts.xml.gz</loc>\n', 'utf-8'))
sitemap_base.write(bytes('\t</sitemap>\n', 'utf-8'))

sitemap_base.write(bytes('</sitemapindex>\n', 'utf-8'))

sitemap_base.seek(os.SEEK_SET)

sm_posts = app.models.Sitemap('sitemap.xml', datetime.now(), sitemap_base)
sm_posts.save()
sitemap_base.close()
