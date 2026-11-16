# syntax=docker/dockerfile:1
# Didebaan — React console image: build once with Node, serve with nginx.
# Build context: ./frontend

FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Empty VITE_API_BASE keeps requests same-origin; nginx proxies /api to Django.
ARG VITE_API_BASE=""
ARG VITE_ENVIRONMENT=production
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_ENVIRONMENT=${VITE_ENVIRONMENT}

RUN npm run build


FROM nginx:1.27-alpine AS runtime

RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
