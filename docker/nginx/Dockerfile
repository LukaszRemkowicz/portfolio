FROM nginx:1.29-alpine

COPY infra/nginx/static_server.conf /etc/nginx/nginx.conf
COPY frontend/z public/error.html /usr/share/nginx/html/error.html
