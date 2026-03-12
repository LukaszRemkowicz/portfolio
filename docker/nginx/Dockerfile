FROM nginx:latest

# Copy the Nginx template into the image
# This ensures that routing logic is versioned along with the image
COPY nginx/TEMPLATE.conf /etc/nginx/templates/nginx.conf.template

# Note: The official Nginx image's entrypoint automatically runs envsubst
# on files in /etc/nginx/templates/ and outputs them to /etc/nginx/conf.d/
# OR wherever NGINX_ENVSUBST_OUTPUT_DIR points.
