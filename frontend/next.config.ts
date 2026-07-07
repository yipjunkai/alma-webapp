import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";

// Next injects inline bootstrap scripts and styles; dev/HMR additionally needs
// `eval`. Everything else is locked to same-origin.
const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self' data:",
  "connect-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone) for a small Docker image.
  output: "standalone",
  async headers() {
    return [
      {
        source: "/:path*",
        // Apply to top-level document responses only. React Server Component
        // navigation / router.refresh() payloads carry the `RSC` request header
        // and abort if these headers (esp. nosniff on text/x-component) are set
        // on them — so skip those. Documents are what a scanner checks anyway.
        missing: [{ type: "header", key: "RSC" }],
        headers: securityHeaders,
      },
    ];
  },
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
