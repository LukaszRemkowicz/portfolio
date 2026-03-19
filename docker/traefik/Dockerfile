FROM traefik:latest

# Install apache2-utils for htpasswd and gettext for envsubst.
RUN apk add --no-cache apache2-utils gettext

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["traefik"]
