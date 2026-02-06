# =========================================================================
# Jorge's Real Estate AI Platform - Next.js Frontend Dockerfile
# Optimized for production deployment with mobile excellence features
# =========================================================================

# Use official Node.js LTS image as base
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Install dependencies needed for native modules
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# =========================================================================
# Dependencies Stage
# =========================================================================
FROM base AS deps
# Install dependencies
RUN npm ci --only=production

# =========================================================================
# Builder Stage
# =========================================================================
FROM base AS builder

# Copy source code
COPY . .

# Install all dependencies (including dev dependencies)
RUN npm ci

# Set production environment variables for build
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# =========================================================================
# Production Stage
# =========================================================================
FROM base AS runner

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application from builder stage
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Copy service worker and PWA files
COPY --from=builder /app/public/sw.js ./public/
COPY --from=builder /app/public/manifest.json ./public/

# Set correct ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Set hostname
ENV HOSTNAME="0.0.0.0"

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application
CMD ["node", "server.js"]