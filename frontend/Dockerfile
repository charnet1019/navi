# Multi-stage build for Vue.js frontend
# Stage 1: Builder - Build the application
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_CSRF_COOKIE_NAME=navi_csrf_token
ARG VITE_CSRF_HEADER_NAME=X-CSRF-Token
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_CSRF_COOKIE_NAME=$VITE_CSRF_COOKIE_NAME
ENV VITE_CSRF_HEADER_NAME=$VITE_CSRF_HEADER_NAME

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy application source
COPY . .

# Build the application
RUN npm run build

# Stage 2: Runtime - Serve with Nginx
FROM nginx:1.25-alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user for security
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
