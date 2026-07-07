# Coding-agent usage

## Writeup

**Tooling.** This app was built with **Claude Code** driving a **multi-agent orchestration**
pattern rather than a single chat loop: a lead session decomposed the work, spawned parallel
sub-agents each scoped to an isolated slice, and then *verified* their output before integrating it.
Because the stack is deliberately bleeding-edge — Next.js 16, React 19, Tailwind v4 — the agents
were forbidden from relying on model memory for framework APIs and made to check **Context7** and
the in-repo `AGENTS.md` guides instead (the frontend guide opens with a blunt *"This is NOT the
Next.js you know — read the docs before writing any code"*). Most of the build ran on **Claude Fable
5**; the review-and-remediation pass ran on **Claude Opus 4.8**.

**What I delegated vs. wrote by hand.** I (the human) owned the **decisions and the contract**; the
agents owned the **typing**. I chose the architecture (FastAPI owns all logic, Next.js is pure
presentation), the storage/email/auth trade-offs (SQLite + Alembic, Resend + console fallback, a
backend-issued JWT cookie), and — critically — I wrote a **fixed API contract up front** so that
parallel agents building the frontend and backend in isolation couldn't drift apart. I also wrote
the three `AGENTS.md` guides that constrain how every agent works in this repo (golden-rule verify
gates, "routers stay thin," "no Server Actions," the Base UI gotchas). The agents then generated, in
parallel: the `frontend/` + `backend/` restructure, the entire FastAPI backend and its pytest suite,
the public form / login / admin UI, the Playwright e2e harness, the Docker + CI setup, and the
property-based test layer. Every design doc, this file, and all remediation fixes I directed and
applied hands-on.

The split is deliberate: the **judgment calls are where the value and the risk concentrate**, so I
kept those; the mechanical breadth — CRUD wiring, boilerplate, test scaffolding — is exactly what
agents do quickly and well, especially fanned out in parallel. The force-multiplier wasn't "agent
writes code," it was **agent writes code, second agent tries to break it** — which is where the two
best catches came from.

**Where the agent was subtly wrong (and how I caught it).** The restructure agent moved the Next
app into `frontend/`, rewrote CI into three jobs, and reported *"pnpm verify + build + e2e all
green."* They were — but only **locally**. `pnpm/action-setup@v4`, given no explicit `version`,
resolves the pnpm version from the `packageManager` field of the **repo-root** `package.json` —
which no longer existed after everything moved into `frontend/`. So on a fresh GitHub runner the
frontend and e2e jobs would have failed at the pnpm-setup step, *before any test ran*. The config
looked right and passed every local check, which is exactly what made it dangerous. It wasn't caught
by me eyeballing the YAML — it was caught by a **CI-lens reviewer agent** in the adversarial pass,
confirmed by an independent verifier, and fixed by pinning `package_json_file: frontend/package.json`
in both jobs (commit `dd6747e`). The lesson I encoded going forward: *"the agent says it's green" is
not "the environment that will run it is green" — verify the claim, not the summary.*

That same adversarial pass caught a second, worse one: a committed default JWT secret
(`dev-secret-change-me`) that would have let anyone forge an attorney session. It's now an ephemeral
per-process key with a fail-fast startup check on weak values (commit `2285bf1`). And later, the
**property-based tests I had an agent add found real robustness bugs** an example-based suite missed
— e.g. a lone Unicode surrogate in a login password (arriving as a JSON `\uXXXX` escape) crashing
credential verification with a 500 instead of returning a clean 401 (commit `7a0c161`). Three
separate defects, all surfaced by agents pointed at *breaking* the code rather than writing it.

## Representative prompts (excerpts)

**The fixed API contract handed to both build agents (so parallel work couldn't drift):**

> All backend routes live under `/api`. `POST /api/leads` (PUBLIC, multipart) validates
> first_name/last_name/email + resume (.pdf/.doc/.docx, ≤5 MB, streamed), persists as `PENDING`,
> then via BackgroundTasks emails prospect + attorney — an email failure must never fail the
> request. `GET /api/leads` (AUTH, paginated) … `PATCH /api/leads/{id}`: PENDING→REACHED_OUT
> allowed, same-state idempotent 200, otherwise 409 … Auth = env-seeded attorney, HS256 JWT in an
> httpOnly `alma_session` cookie …

**Backend build agent (excerpt):**

> Build a complete, production-quality FastAPI backend … routers stay thin, services own logic …
> tests use DI overrides so email is captured, never sent … iterate until `uv run ruff check . &&
> ruff format --check . && pyright && pytest` is green, then run a live curl flow
> (create → login → list → PATCH → download) before reporting.

**Adversarial review workflow (excerpt):**

> Five parallel reviewers, one lens each — correctness / security / requirements-compliance /
> repo-quality / run-the-README-on-a-clean-checkout. Every finding is then re-checked by an
> independent skeptic agent whose default stance is *refuted until the code proves otherwise*; a
> finding survives only on a majority. Do not report a documented, deliberate scope cut as a bug.

Full orchestration scripts and transcripts are preserved from the session.

## Attribution

Everything here is Claude-assisted; the table below is the honest split of who owned what. There is
no separate hand-written vs. generated marker in individual commit trailers — this table (plus the
descriptive commit history) is the record of record.

| Area                                                          | Origin                              |
| ------------------------------------------------------------- | ----------------------------------- |
| Architecture, API contract, storage/email/auth decisions      | **Human-directed**                  |
| The three `AGENTS.md` agent-guidance files                     | **Human-written**                   |
| Repo restructure (`frontend/` + `backend/`, CI, task runner)   | Agent-generated, human-reviewed     |
| FastAPI backend (`backend/app`, migrations, pytest suite)      | Agent-generated, human-reviewed     |
| Public form, login, admin queue (`frontend/src`)               | Agent-generated, human-reviewed     |
| Playwright e2e + property-based (Hypothesis / fast-check) tests | Agent-generated, human-reviewed     |
| Docker, compose, hardened CI (SHA-pinned, Scorecard)           | Agent-generated, human-reviewed     |
| Adversarial review that found the CI break + JWT-secret issue  | Agent-generated (multi-agent), human-triaged |
| Remediation fixes (security, correctness, CI, docs)            | **Human-directed**, hand-applied    |
| `README.md`, `docs/DESIGN.md`, this file                       | **Human-written**                   |

The Next.js scaffold + toolchain (Vitest / Playwright / ESLint / Prettier / CI) predates this build
and was set up in an earlier session, also with Claude Code.
