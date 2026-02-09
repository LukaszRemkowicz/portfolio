#!/bin/sh
set -e

# 1. Preserve Webpack-generated index.html while copying static assets from public/
# This prevents overwriting the index.html that has script tags injected by Webpack
mv dist/index.html dist/_index.html
cp -r public/* dist/
mv dist/_index.html dist/index.html

# 2. Replace placeholders in all SEO and metadata files
# We target index.html (for OG/Twitter/JSON-LD/Analytics), sitemap.xml, and robots.txt
# Using a temp file approach for cross-platform 'sed' compatibility (Mac/Linux)
for file in dist/index.html dist/sitemap.xml dist/robots.txt; do
    if [ -f "$file" ]; then
        echo "Updating placeholders in $file..."
        sed "s/__SITE_DOMAIN__/${SITE_DOMAIN}/g" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        sed "s/__GA_TRACKING_ID__/${GA_TRACKING_ID}/g" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    fi
done
