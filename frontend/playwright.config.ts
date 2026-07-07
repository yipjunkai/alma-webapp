import { defineConfig, devices } from "@playwright/test";

const baseURL = "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Boot the FastAPI backend against an isolated, throwaway database and
      // upload dir so e2e runs never touch dev data. An empty RESEND_API_KEY
      // keeps emails in console mode.
      command:
        "rm -f data/e2e.db && rm -rf data/e2e-uploads && uv run alembic upgrade head && uv run uvicorn app.main:app --port 8000",
      cwd: "../backend",
      env: {
        DATABASE_URL: "sqlite:///./data/e2e.db",
        UPLOAD_DIR: "./data/e2e-uploads",
        RESEND_API_KEY: "",
        // Pin the admin identity the spec signs in with, so a customized
        // backend/.env can't make e2e fail with a spurious 401.
        ADMIN_EMAIL: "attorney@example.com",
        ADMIN_PASSWORD: "changeme",
      },
      url: "http://127.0.0.1:8000/api/health",
      // Always boot the isolated stack — never reuse a dev server, or e2e would
      // silently write into the dev database and skip the production build.
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      // Build + serve the production app so tests run against real output.
      command: "pnpm run build && pnpm run start",
      url: baseURL,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
