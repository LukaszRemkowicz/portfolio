FROM nginx:latest

# Copy the Nginx template into the image
# This ensures that routing logic is versioned along with the image
COPY nginx/TEMPLATE.conf /etc/nginx/templates/nginx.conf.template

# Copy shared include templates — the official nginx entrypoint script
# (20-envsubst-on-templates.sh) processes ALL *.template files in
# /etc/nginx/templates/ and outputs them preserving directory structure,
# so these render to /etc/nginx/includes/*.conf at container start.
COPY nginx/includes/ /etc/nginx/templates/includes/

# Note: The official Nginx image's entrypoint automatically runs envsubst
# on files in /etc/nginx/templates/ and outputs them to /etc/nginx/conf.d/
# OR wherever NGINX_ENVSUBST_OUTPUT_DIR points.
