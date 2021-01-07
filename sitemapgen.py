from datetime import datetime

import app.models

import tempfile
import gzip
import os

def date2rss(pub):
    ctime = pub.ctime()
    return (f'{ctime[0:3]}, {pub.day:02d} {ctime[4:7]}' + pub.strftime(' %Y %H:%M:%S %z'))


# Posts

posts = app.models.Post.all(page=0, limit=-1)['Posts']

#
# RSS
#

rss_posts = tempfile.TemporaryFile()
rss_posts.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
rss_posts.write(bytes('<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:sy="http://purl.org/rss/1.0/modules/syndication/" xmlns:slash="http://purl.org/rss/1.0/modules/slash/" >\n', 'utf-8'))
rss_posts.write(bytes('\n', 'utf-8'))
rss_posts.write(bytes('<channel>\n', 'utf-8'))
rss_posts.write(bytes('<title>From pet to cattle</title>\n', 'utf-8'))
rss_posts.write(bytes('<atom:link href="https://pet2cattle.com/sitemap.rss" rel="self" type="application/rss+xml" />\n', 'utf-8'))
rss_posts.write(bytes('<link>https://pet2cattle.com</link>\n', 'utf-8'))
rss_posts.write(bytes('<description>Tu referencia para la administración de sistemas</description>\n', 'utf-8'))
rss_posts.write(bytes('<lastBuildDate>'+date2rss(datetime.now())+'</lastBuildDate>\n', 'utf-8'))
rss_posts.write(bytes('<language>en-US</language>\n', 'utf-8'))
rss_posts.write(bytes('<sy:updatePeriod>daily</sy:updatePeriod>\n', 'utf-8'))
rss_posts.write(bytes('<sy:updateFrequency>1</sy:updateFrequency>\n', 'utf-8'))
rss_posts.write(bytes('<generator>https://github.com/jordiprats/flask-pet2cattle</generator>\n', 'utf-8'))
rss_posts.write(bytes('\n', 'utf-8'))

for post in posts:
    rss_posts.write(bytes('\t<item>\n', 'utf-8'))
    rss_posts.write(bytes('\t\t<title>'+post.get_title()+'</title>\n', 'utf-8'))
    rss_posts.write(bytes('\t\t<link>https://pet2cattle.com'+post.url+'</link>\n', 'utf-8'))
    rss_posts.write(bytes('\t\t<pubDate>'+date2rss(post.get_last_modified())+'</pubDate>\n', 'utf-8'))
    rss_posts.write(bytes('\t\t<description><![CDATA['+post.get_excerpt()+']]></description>\n', 'utf-8'))
    rss_posts.write(bytes('\t\t<guid isPermaLink="true">https://pet2cattle.com'+post.url+'</guid>\n', 'utf-8'))
    rss_posts.write(bytes('\t</item>\n', 'utf-8'))

rss_posts.write(bytes('</channel>\n', 'utf-8'))
rss_posts.write(bytes('</rss>\n', 'utf-8'))
rss_posts.seek(os.SEEK_SET)
print(rss_posts.read().decode('utf-8'))

rss_posts.seek(os.SEEK_SET)
sm_posts_rss = app.models.Sitemap('sitemap.rss', datetime.now(), rss_posts)
sm_posts_rss.save()
rss_posts.close()

#
# sitemap posts
#

tmp_sitemap_posts = tempfile.TemporaryFile()
with gzip.open(filename=tmp_sitemap_posts, mode='wb') as sitemap_posts:
    sitemap_posts.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
    sitemap_posts.write(bytes('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n', 'utf-8'))
    for post in posts:
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

#
# sitemap pages
#

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

#
# sitemap index
#

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
