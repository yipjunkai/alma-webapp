import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Unmount React trees between tests (RTL auto-cleanup needs the global
// afterEach, which we register explicitly since `globals` is off).
afterEach(() => {
  cleanup();
});
