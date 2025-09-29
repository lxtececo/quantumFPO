#!/bin/sh
# Custom entrypoint for non-root nginx execution

echo "Starting nginx in non-root mode..."

# Create necessary temporary directories if they don't exist
mkdir -p /tmp/nginx-client-temp /tmp/nginx-proxy-temp /tmp/nginx-fastcgi-temp /tmp/nginx-uwsgi-temp /tmp/nginx-scgi-temp

# Add hosts fallback for backend service to prevent startup DNS resolution failure
# In production Kubernetes, the real service DNS will take precedence
echo "127.0.0.1 quantumfpo-java-backend" >> /etc/hosts
echo "Added hosts fallback for quantumfpo-java-backend"

# Start nginx
exec nginx -g "daemon off;"