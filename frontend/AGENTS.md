<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

<!-- END:nextjs-agent-rules -->

# Alma web app — agent guide (frontend)

A Next.js 16 (App Router) web application. Keep this file accurate as the project evolves.

## Golden rule

Run `pnpm verify` before considering any change done. It runs typecheck + lint + format check + unit tests and mirrors CI exactly. Never leave the tree red.

## Commands (pnpm — do not use npm or yarn)

| Command                             | Purpose                                 |
| ----------------------------------- | --------------------------------------- |
| `pnpm dev`                          | Dev server (Turbopack)                  |
| `pnpm build` / `pnpm start`         | Production build / serve                |
| `pnpm verify`                       | typecheck + lint + format:check + unit  |
| `pnpm test` / `pnpm test:watch`     | Vitest once / watch                     |
| `pnpm test:e2e`                     | Playwright e2e (builds prod, then runs) |
| `pnpm lint` / `pnpm lint:fix`       | ESLint                                  |
| `pnpm format` / `pnpm format:check` | Prettier                                |
| `pnpm typecheck`                    | `tsc --noEmit`                          |

## Stack

- **Next.js 16** App Router + **React 19** — React Server Components by default
- **TypeScript** (strict); path alias `@/*` → `src/*`
- **Tailwind CSS v4** (CSS-config; tokens in `src/app/globals.css`)
- **shadcn/ui** (base-nova style, built on **Base UI**) in `src/components/ui`
- **Vitest** + Testing Library (unit); **Playwright** (e2e)
- **pnpm**; ESLint (flat config) + Prettier

## Conventions

- **Server Components by default.** Add `"use client"` only for interactivity, hooks, or browser APIs. Fetch on the server (forwarding the `alma_session` cookie); mutate by calling the FastAPI `/api/*` routes through the helpers in `src/lib/api.ts`. This app does **not** use Server Actions — all mutations go to the backend.
- **Data:** All data lives in the FastAPI backend (`../backend`). The frontend calls it through the `/api/*` rewrite in `next.config.ts`; the auth cookie (`alma_session`) is set by the backend. Never duplicate backend business logic in the frontend.
- **Styling:** use theme tokens (`bg-background`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring`) — never ad-hoc hex. Compose shadcn primitives (`Table`, `Dialog`, `Sheet`, `Card`, …) instead of raw elements.
- **Components:** named exports for shared components; default export only for route files (`page.tsx`, `layout.tsx`). Keep files small and colocated.

## Routes

| Route          | What                                                                                                                                                              |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`            | Public lead intake form. Server `page.tsx` + client `src/components/lead-form.tsx` (validation, 422 mapping, success state).                                      |
| `/login`       | Attorney login. Server page checks `GET /api/auth/me` (forwarding `alma_session`) and redirects to `/admin/leads` if already signed in.                           |
| `/admin/leads` | Server-component queue: forwards the cookie to `GET /api/leads` (`cache: "no-store"`), passes `?state=` through, redirects to `/login` on 401. Empty state, tabs. |

`src/proxy.ts` (Next 16 proxy, ex-middleware) redirects cookie-less `/admin/*` requests to `/login` — UX only; the backend is the real enforcement.

## API client (`src/lib/api.ts`)

`Lead`/`LeadListResponse` types plus thin helpers: `createLead`, `login`, `logout`, `markReachedOut` (browser, same-origin `/api/*` via the rewrite) and `fetchLeads`, `fetchMe` (server, hit `BACKEND_URL` directly and take a forwarded cookie header). `fieldErrorsFromDetail` maps FastAPI 422 `detail` arrays to per-field errors. Date helpers live in `src/lib/format.ts` (backend timestamps are UTC, sometimes without `Z`).

## Repo-specific gotchas (don't re-break these)

- Route `params` are **`Promise<...>`** — `await` them before use.
- shadcn **`Button` is Base UI — there is no `asChild`.** To style a link as a button, apply `buttonVariants({ ... })` with `cn()` to the element directly.
- Fonts: reference `var(--font-geist-sans)` / `var(--font-geist-mono)` in `@theme inline`. Never reintroduce a circular `--font-sans: var(--font-sans)`.
- pnpm blocks dependency build scripts by default; approved ones are listed under `package.json` → `pnpm.onlyBuiltDependencies`.

## Testing

- **Unit (Vitest):** pure logic and domain rules (e.g. SLA/deadline math, status transitions). Colocate as `src/**/*.test.ts(x)`.
- **Component (RTL):** interactive client components.
- **E2E (Playwright):** happy-path flows in `e2e/*.spec.ts`.
- **Async Server Components can't be unit-tested** (Vitest limitation) — cover them with e2e.
- Test the risky and pure parts, not trivia. Not dogmatic TDD.

## Working style

- Build in **thin vertical slices**; keep the app runnable and demo-able at every commit.
- Propose a short plan + trade-offs before large changes; prefer extending existing patterns over adding dependencies.
- Make **small, labeled commits**. Call out anything cut for time.
