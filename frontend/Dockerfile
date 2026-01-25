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
FROM node:20-alpine AS prod
WORKDIR /app
RUN npm install -g serve
USER node
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
