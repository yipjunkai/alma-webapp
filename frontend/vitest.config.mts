import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  // `tsconfigPaths` resolves the `@/*` alias; `react` enables JSX/TSX.
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // Unit/component tests live next to source as `*.test.ts(x)`.
    // Playwright specs live in `e2e/` and are handled separately.
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
