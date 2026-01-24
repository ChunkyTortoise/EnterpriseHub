import type { NextConfig } from "next";
import withPWA from "next-pwa";

const nextConfig: NextConfig = {
  // Enable Turbopack for Next.js 16 compatibility
  turbopack: {},

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false,
  },

  // Experimental features for app directory (if needed)
  experimental: {
    // Remove appDir as it's stable in Next.js 16
  }
};

// Configure PWA settings for Jorge's Real Estate AI Platform
const pwaConfig = withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https?.*/,
      handler: "NetworkFirst",
      options: {
        cacheName: "jorge-ai-api-cache",
        expiration: {
          maxEntries: 32,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
      },
    },
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
      handler: "CacheFirst",
      options: {
        cacheName: "jorge-ai-images",
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        },
      },
    },
  ],
});

export default pwaConfig(nextConfig);
