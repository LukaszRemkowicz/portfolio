FROM nginx:1.31.3-alpine

RUN apk add --no-cache tzdata
ENV TZ=Europe/Warsaw

COPY infra/nginx/static_server.conf /etc/nginx/nginx.conf
COPY infra/nginx/includes /etc/nginx/includes
COPY infra/nginx/html/error.html /usr/share/nginx/html/error.html
COPY infra/nginx/html/404.html /usr/share/nginx/html/404.html
COPY infra/nginx/templates /etc/nginx/text-resources/templates
COPY docker/nginx/18-render-text-resources.sh /docker-entrypoint.d/18-render-text-resources.sh
RUN chmod +x /docker-entrypoint.d/18-render-text-resources.sh
