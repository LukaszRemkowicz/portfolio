FROM nginx:1.29-alpine

RUN apk add --no-cache tzdata
ENV TZ=Europe/Warsaw

COPY docker/nginx/docker-entrypoint.d/prepare-log-files.sh /docker-entrypoint.d/prepare-log-files.sh
RUN chmod +x /docker-entrypoint.d/prepare-log-files.sh

COPY infra/nginx/static_server.conf /etc/nginx/nginx.conf
COPY infra/nginx/includes /etc/nginx/includes
COPY frontend/public/error.html /usr/share/nginx/html/error.html
COPY frontend/public/404.html /usr/share/nginx/html/404.html
