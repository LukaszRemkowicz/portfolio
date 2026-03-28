# --- Base deps ---
FROM node:24-alpine AS base
WORKDIR /app
RUN npm install -g npm@latest && apk add --no-cache tzdata
ENV TZ=Europe/Warsaw

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
# TODO: fix it to api site domain
ARG API_URL=https://api.portfolio.local
ARG GA_TRACKING_ID
ARG SENTRY_DSN_FE
ARG ENVIRONMENT=production
ARG ALLOWED_HOSTS
ARG PROJECT_OWNER

ENV SITE_DOMAIN=$SITE_DOMAIN
ENV VITE_API_URL=$API_URL
ENV VITE_GA_TRACKING_ID=$GA_TRACKING_ID
ENV VITE_SENTRY_DSN_FE=$SENTRY_DSN_FE
ENV VITE_ENVIRONMENT=$ENVIRONMENT
ENV ALLOWED_HOSTS=$ALLOWED_HOSTS
ENV PROJECT_OWNER=$PROJECT_OWNER

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build:ssr && \
    node ./scripts/inject-static-metadata.mjs

FROM node:24-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=8080

COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
COPY --from=build /app/server ./server
COPY --from=build /app/scripts ./scripts

USER node

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- "http://127.0.0.1:${PORT}/health" >/dev/null || exit 1
CMD ["npm", "run", "serve:ssr"]

FROM runtime AS prod
