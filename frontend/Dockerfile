# ==============================================================================
# ClinSaarthi AI - Frontend Multi-Stage Dockerfile
# Stage 1: Compile TypeScript & Vite SPA production bundle
# Stage 2: Serve static bundle via high-performance Nginx reverse proxy
# ==============================================================================

# --- Stage 1: Build Environment ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install npm dependencies cleanly
RUN npm ci

# Copy full frontend application source
COPY . .

# Compile TypeScript and Vite production assets
RUN npm run build

# --- Stage 2: Production Nginx Server ---
FROM nginx:1.25-alpine AS runner

# Remove default nginx boilerplate
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SSE buffering disabled & API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose standard HTTP port
EXPOSE 80

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/healthz || exit 1

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
