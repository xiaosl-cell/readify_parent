FROM nginx:alpine

COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Replace API_BASE_URL in config.js at container startup
# so the frontend calls /api/v1 (proxied by nginx) instead of localhost:8082
COPY js/config.js /usr/share/nginx/html/js/config.js.template
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-config-env.sh && \
    echo 'sed "s|http://localhost:8082/api/v1|/api/v1|g" /usr/share/nginx/html/js/config.js.template > /usr/share/nginx/html/js/config.js' >> /docker-entrypoint.d/30-config-env.sh && \
    chmod +x /docker-entrypoint.d/30-config-env.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
