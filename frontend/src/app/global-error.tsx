"use client";

import * as React from "react";

import "./globals.css";

// Replaces the root layout when it (or a shared boundary) throws, so it renders
// its own <html>/<body>. Kept minimal and self-contained.
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="flex min-h-svh flex-col items-center justify-center gap-4 px-6 text-center antialiased">
        <h1 className="text-xl font-semibold tracking-tight">
          Something went wrong
        </h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          A critical error occurred. Please refresh the page to continue.
        </p>
        <button
          onClick={reset}
          className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background"
        >
          Try again
        </button>
      </body>
    </html>
  );
}
