FROM nginx:1.29-alpine

RUN apk add --no-cache tzdata
ENV TZ=Europe/Warsaw

COPY infra/nginx/static_server.conf /etc/nginx/nginx.conf
COPY frontend/public/error.html /usr/share/nginx/html/error.html
