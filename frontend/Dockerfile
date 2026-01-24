# --- Base deps ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- Development ---
FROM base AS dev
COPY . .
RUN chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "start"]

# --- Production build ---
FROM base AS build
ARG SITE_DOMAIN=portfolio.local
ENV SITE_DOMAIN=$SITE_DOMAIN
COPY . .
RUN npm run build && ./scripts/inject-metadata.sh

# --- Production runtime ---
FROM node:20-alpine AS prod
WORKDIR /app
RUN npm install -g serve
USER node
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
