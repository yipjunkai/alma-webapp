import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // `react` enables JSX/TSX; Vite resolves the `@/*` alias from tsconfig natively.
  plugins: [react()],
  resolve: { tsconfigPaths: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // Unit/component tests live next to source as `*.test.ts(x)`.
    // Playwright specs live in `e2e/` and are handled separately.
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
