#!/bin/sh
set -e

# 1. Preserve Webpack-generated index.html while copying static assets from public/
# This prevents overwriting the index.html that has script tags injected by Webpack
mv dist/index.html dist/_index.html
cp -r public/* dist/
mv dist/_index.html dist/index.html

# 2. Inject the Sitemap URL into robots.txt for SEO
echo "Sitemap: https://${SITE_DOMAIN}/sitemap.xml" >> dist/robots.txt

# 3. Replace the placeholder in sitemap.xml with the actual domain
sed -i "s/__SITE_DOMAIN__/${SITE_DOMAIN}/g" dist/sitemap.xml
