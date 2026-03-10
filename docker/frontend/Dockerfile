# --- Base deps ---
FROM node:20-alpine AS base
WORKDIR /app
RUN npm install -g npm@latest

# --- Development ---
FROM base AS dev
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN chown -R node:node /app
USER node

EXPOSE $FRONTEND_PORT
CMD ["npm", "run", "dev"]

# --- Production build ---
FROM base AS build
ARG SITE_DOMAIN
ARG API_URL=https://api.portfolio.local
ARG GA_TRACKING_ID
ARG SENTRY_DSN_FE
ARG ENVIRONMENT=production
ARG ALLOWED_HOSTS

ENV SITE_DOMAIN=$SITE_DOMAIN
ENV VITE_API_URL=$API_URL
ENV VITE_GA_TRACKING_ID=$GA_TRACKING_ID
ENV VITE_SENTRY_DSN_FE=$SENTRY_DSN_FE
ENV VITE_ENVIRONMENT=$ENVIRONMENT
ENV ALLOWED_HOSTS=$ALLOWED_HOSTS

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
# The script is now inside the frontend context directly
RUN npm run build && ./scripts/inject-metadata.sh && rm -rf ./scripts

# --- Production runtime ---
FROM nginx:alpine AS prod
WORKDIR /usr/share/nginx/html

# Create non-root user for nginx
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Copy built assets
COPY --from=build /app/dist .

# Copy internal nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Use non-root user
USER nginx

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
