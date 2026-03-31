FROM traefik:latest

# Install apache2-utils for htpasswd, gettext for envsubst, and tzdata so
# file-based access logs can render in the configured local timezone.
RUN apk add --no-cache apache2-utils gettext tzdata

ENV TZ=Europe/Warsaw

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["traefik"]
