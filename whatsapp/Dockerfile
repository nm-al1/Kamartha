FROM node:26-bookworm-slim
ENV PUPPETEER_SKIP_DOWNLOAD=true CHROME_PATH=/usr/bin/chromium BRIDGE_HOST=0.0.0.0
RUN apt-get update && apt-get install -y --no-install-recommends chromium ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY whatsapp/package.json whatsapp/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts && install -d -m 0700 -o node -g node /app/.state
COPY whatsapp/*.mjs ./
USER node
EXPOSE 3001
CMD ["node", "bridge.mjs"]
