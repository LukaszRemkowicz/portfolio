# --- Base deps ---
FROM node:20-alpine AS base
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install -g npm@latest && npm ci

# --- Development ---
FROM base AS dev
COPY frontend/ .
RUN chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- Production build ---
FROM base AS build
ARG SITE_DOMAIN
ARG API_URL=https://api.portfolio.local
ARG GA_TRACKING_ID
ARG SENTRY_DSN_FE
ARG ENVIRONMENT=production

ENV SITE_DOMAIN=$SITE_DOMAIN
ENV VITE_API_URL=$API_URL
ENV VITE_GA_TRACKING_ID=$GA_TRACKING_ID
ENV VITE_SENTRY_DSN_FE=$SENTRY_DSN_FE
ENV VITE_ENVIRONMENT=$ENVIRONMENT

COPY frontend/ .
COPY scripts/frontend/inject-metadata.sh ./scripts/

RUN npm run build && ./scripts/inject-metadata.sh && rm -rf ./scripts

# --- Production runtime ---
FROM nginx:alpine AS prod
WORKDIR /usr/share/nginx/html

# Copy built assets
COPY --from=build /app/dist .

# Copy internal nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
