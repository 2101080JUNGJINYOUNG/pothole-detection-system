FROM nginx:alpine

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

