# --- Base image ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- Development image ---
FROM base AS dev
COPY . .
EXPOSE 3000
RUN chown -R node:node /app
USER node
CMD ["npm", "start"]

# --- Production build ---
FROM base AS build
COPY . .
RUN npm run build

# --- Test image ---
FROM base AS test
COPY . .
CMD ["npm", "test", "--", "--passWithNoTests"]

# --- Production runtime ---
FROM node:20-alpine AS prod
WORKDIR /app
RUN npm install -g serve
USER node
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]

# --- Final stage switcher ---
ARG NODE_ENV=development
FROM dev AS final-dev
FROM prod AS final-prod

# Use the right final stage
# docker build --target final-prod --build-arg NODE_ENV=production .
