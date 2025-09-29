# Multi-stage build for React + Vite frontend
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install ALL dependencies (including devDependencies needed for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Install curl for health checks and create directories
RUN apk add --no-cache curl && \
    # Create nginx cache directories with proper permissions
    mkdir -p /tmp/nginx-client-temp \
             /tmp/nginx-proxy-temp \
             /tmp/nginx-fastcgi-temp \
             /tmp/nginx-uwsgi-temp \
             /tmp/nginx-scgi-temp \
             /var/cache/nginx \
             /var/log/nginx \
             /var/run/nginx && \
    # Set ownership and permissions for nginx user
    chown -R nginx:nginx /tmp/nginx-* /var/cache/nginx /var/log/nginx /var/run/nginx && \
    chmod -R 755 /tmp/nginx-* /var/cache/nginx /var/log/nginx /var/run/nginx

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configurations
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx-nonroot.conf /etc/nginx/nginx.conf

# Copy and setup custom entrypoint script
COPY docker-entrypoint-custom.sh /docker-entrypoint-custom.sh
RUN chmod +x /docker-entrypoint-custom.sh

# Set environment variable for worker processes (optimized for Kubernetes)
ENV NGINX_WORKER_PROCESSES=2

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Use custom entrypoint that sets worker processes before starting nginx
ENTRYPOINT ["/docker-entrypoint-custom.sh"]
CMD ["nginx", "-g", "daemon off;"]