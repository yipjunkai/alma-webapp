import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone) for a small Docker image.
  output: "standalone",
  // Proxy API calls to the FastAPI backend (../backend) during dev and prod.
  // NOTE: the destination is baked at build time, so BACKEND_URL must be set as a
  // build arg for containers (see frontend/Dockerfile) — not just at runtime.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
