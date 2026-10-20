FROM node:22-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund

FROM deps AS demo
COPY server ./server
USER node
CMD ["node", "server/demo-gateway-adapter.js"]

FROM deps AS builder
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS office
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
# Keep the locked build dependencies: Next loads next.config.ts using TypeScript.
# This avoids installing dependencies at startup in this first local demo.
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/server ./server
COPY --from=builder /app/package.json /app/next.config.ts /app/LICENSE ./
RUN mkdir -p /data/hermes && chown -R node:node /data /app/.next
USER node
EXPOSE 3000
CMD ["node", "server/index.js"]
