# --- Base deps ---
FROM node:20-alpine AS base
WORKDIR /app
# Note: We don't copy node_modules, we let volume handle it or install fresh
# checking for package.json changes
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# --- Development ---
FROM base AS dev
COPY frontend/ .
RUN chown -R node:node /app
USER node
EXPOSE 3000
# Vite needs host binding
CMD ["npm", "run", "start", "--", "--host"]

# --- Production build ---
FROM base AS build
ARG SITE_DOMAIN=portfolio.local
ARG API_URL=https://api.portfolio.local
ARG SSL_KEY_PATH
ARG SSL_CRT_PATH
ARG GA_TRACKING_ID
ENV SITE_DOMAIN=$SITE_DOMAIN
ENV API_URL=$API_URL
ENV SSL_KEY_PATH=$SSL_KEY_PATH
ENV SSL_CRT_PATH=$SSL_CRT_PATH
ENV GA_TRACKING_ID=$GA_TRACKING_ID
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
