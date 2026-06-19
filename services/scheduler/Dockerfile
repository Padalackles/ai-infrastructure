# ──────────────────────────────────────────────
# Scheduler Service — Production Image
# ──────────────────────────────────────────────

FROM node:22-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json tsconfig.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build
RUN npm ci --omit=dev

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/node_modules ./node_modules
COPY --from=builder /build/package.json ./
COPY config.yaml ./
USER node
CMD ["node", "dist/index.js"]
