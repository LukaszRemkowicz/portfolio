# --- Base deps ---
FROM node:20-alpine AS base
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# --- Development ---
FROM base AS dev
COPY frontend/ .
RUN chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "start"]

# --- Production build ---
FROM base AS build
ARG SITE_DOMAIN=portfolio.local
ARG API_URL=https://api.portfolio.local
ARG SSL_KEY_PATH
ARG SSL_CRT_PATH
ENV SITE_DOMAIN=$SITE_DOMAIN
ENV API_URL=$API_URL
ENV SSL_KEY_PATH=$SSL_KEY_PATH
ENV SSL_CRT_PATH=$SSL_CRT_PATH
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
