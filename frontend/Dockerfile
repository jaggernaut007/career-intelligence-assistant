# Career Intelligence Assistant - Frontend Dockerfile
# Vite + React + TypeScript

FROM node:20-alpine as base

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# ============================================================================
# Development stage
# ============================================================================
FROM base as development

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]

# ============================================================================
# Build stage
# ============================================================================
FROM base as build

COPY . .

# Build arguments for environment variables
ARG VITE_API_URL
ARG VITE_WS_URL

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

# ============================================================================
# Production stage
# ============================================================================
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Add non-root user and configure nginx to run as non-root
RUN adduser -D -g '' appuser && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

USER appuser

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080 || exit 1

CMD ["nginx", "-g", "daemon off;"]
