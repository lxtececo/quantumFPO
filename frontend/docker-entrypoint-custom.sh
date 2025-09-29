#!/bin/sh
# Custom entrypoint for non-root nginx execution in Kubernetes

echo "Starting nginx in non-root mode..."

# Create necessary temporary directories if they don't exist
mkdir -p /tmp/nginx-client-temp /tmp/nginx-proxy-temp /tmp/nginx-fastcgi-temp /tmp/nginx-uwsgi-temp /tmp/nginx-scgi-temp

# Start nginx directly without the default entrypoint to avoid permission issues
exec nginx -g "daemon off;"