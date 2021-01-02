from datetime import datetime

import app.models

import tempfile
import gzip
import os

# <?xml version="1.0" encoding="UTF-8"?><?xml-stylesheet type="text/xsl" href="http://systemadmin.es/wp-content/plugins/google-sitemap-generator/sitemap.xsl"?>
# <urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#   <url>
# 		<loc>http://systemadmin.es/</loc>
# 		<lastmod>2017-12-21T17:03:10+00:00</lastmod>
# 		<changefreq>daily</changefreq>
# 		<priority>1.0</priority>
# 	</url>
# 	<url>
# 		<loc>http://systemadmin.es/2012/01/generar-un-certificado-autofirmado-con-openssl</loc>
# 		<lastmod>2017-12-21T17:03:10+00:00</lastmod>
# 		<changefreq>monthly</changefreq>
# 		<priority>0.2</priority>
# 	</url>
# </urlset>

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
        sitemap_posts.write(bytes('\t\t<lastmod>'+post.last_modified.strftime("%Y/%m/%d")+'</lastmod>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<changefreq>monthly</changefreq>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t\t<priority>0.5</priority>\n', 'utf-8'))
        sitemap_posts.write(bytes('\t</url>\n', 'utf-8'))
    sitemap_posts.write(bytes('</urlset>', 'utf-8'))

tmp_sitemap_posts.seek(os.SEEK_SET)

sm_posts = app.models.Sitemap('sitemap-posts.xml.gz', datetime.now(), tmp_sitemap_posts)
sm_posts.save()
tmp_sitemap_posts.close()

tmp_sitemap_base = tempfile.TemporaryFile()
with gzip.open(filename=tmp_sitemap_base, mode='wb') as sitemap_base:
    sitemap_base.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'utf-8'))
    sitemap_base.write(bytes('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n', 'utf-8'))
    sitemap_base.write(bytes('\t<sitemap>\n', 'utf-8'))
    sitemap_base.write(bytes('\t\t<loc>https://pet2cattle.com/sitemap-posts.xml</loc>', 'utf-8'))
    sitemap_base.write(bytes('\t</sitemap>\n', 'utf-8'))

tmp_sitemap_base.seek(os.SEEK_SET)

sm_posts = app.models.Sitemap('sitemap.xml.gz', datetime.now(), tmp_sitemap_base)
sm_posts.save()
tmp_sitemap_base.close()

# <?xml version="1.0" encoding="UTF-8"?>
#   <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#     <sitemap>
#       <loc>http://www.example.com/sitemap1.xml.gz</loc>
#     </sitemap>
#     <sitemap>
#       <loc>http://www.example.com/sitemap2.xml.gz</loc>
#     </sitemap>
#   </sitemapindex>
