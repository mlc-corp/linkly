FROM node:22-alpine

WORKDIR /app

# Instalación determinística, solo prod
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Copia código
COPY src ./src

# Variables seguras por defecto (las reales van por runtime)
ENV NODE_ENV=production
EXPOSE 8080

# Usuario no root
USER node

# (Opcional) Healthcheck simple
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["node", "src/server.js"]
