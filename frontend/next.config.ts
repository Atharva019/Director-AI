import type { NextConfig } from "next";

// In production the frontend and API live on different hosts, so the rewrite
// target comes from the environment. Locally it falls back to the dev backend.
const API_ORIGIN = process.env.API_PROXY_ORIGIN ?? "http://127.0.0.1:8000";

// Analysis images are served straight from the public R2 bucket — set this to
// its public hostname (e.g. pub-xxxx.r2.dev, or your own CDN domain).
const R2_HOSTNAME = process.env.NEXT_PUBLIC_R2_HOSTNAME;

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${API_ORIGIN}/api/v1/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      ...(R2_HOSTNAME
        ? [{ protocol: "https" as const, hostname: R2_HOSTNAME }]
        : []),
      {
        protocol: "https" as const,
        hostname: "lh3.googleusercontent.com",
      },
      {
        protocol: "https" as const,
        hostname: "firebasestorage.googleapis.com",
      },
    ],
  },
};

export default nextConfig;
