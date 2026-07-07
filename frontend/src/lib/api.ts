// Thin, typed client for the FastAPI backend.
//
// Browser code calls same-origin `/api/*` paths (rewritten to the backend in
// `next.config.ts`). Server Components call `BACKEND_URL` directly and must
// forward the `alma_session` cookie themselves.

export type LeadState = "PENDING" | "REACHED_OUT";

export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  state: LeadState;
  resume_filename: string;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
}

/** Server-side base URL for the FastAPI backend. */
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export const SESSION_COOKIE = "alma_session";

const GENERIC_ERROR = "Something went wrong. Please try again.";

/** Form fields of the public lead form, matching the backend field names. */
export type LeadFormField = "first_name" | "last_name" | "email" | "resume";

const LEAD_FORM_FIELDS: readonly string[] = [
  "first_name",
  "last_name",
  "email",
  "resume",
];

export type LeadFieldErrors = Partial<Record<LeadFormField, string>>;

/**
 * Map a FastAPI 422 `detail` array onto lead-form field errors. Entries whose
 * `loc` doesn't name a known field (or a malformed payload) fall back to a
 * general form error.
 */
export function fieldErrorsFromDetail(detail: unknown): {
  fieldErrors: LeadFieldErrors;
  formError?: string;
} {
  const fieldErrors: LeadFieldErrors = {};
  let unmapped = false;

  if (Array.isArray(detail)) {
    for (const entry of detail) {
      const loc =
        entry && typeof entry === "object" && Array.isArray(entry.loc)
          ? (entry.loc as unknown[])
          : [];
      const msg =
        entry && typeof entry === "object" && typeof entry.msg === "string"
          ? entry.msg
          : undefined;
      const field = loc.find(
        (part): part is LeadFormField =>
          typeof part === "string" && LEAD_FORM_FIELDS.includes(part),
      );
      if (field && msg) {
        fieldErrors[field] ??= msg;
      } else {
        unmapped = true;
      }
    }
  } else {
    unmapped = true;
  }

  const hasFieldErrors = Object.keys(fieldErrors).length > 0;
  return {
    fieldErrors,
    formError: unmapped || !hasFieldErrors ? GENERIC_ERROR : undefined,
  };
}

export type CreateLeadResult =
  | { ok: true; lead: Lead }
  | { ok: false; fieldErrors: LeadFieldErrors; formError?: string };

/** POST the public lead form (multipart) to the backend. */
export async function createLead(
  formData: FormData,
): Promise<CreateLeadResult> {
  let response: Response;
  try {
    response = await fetch("/api/leads", { method: "POST", body: formData });
  } catch {
    return { ok: false, fieldErrors: {}, formError: GENERIC_ERROR };
  }

  if (response.status === 201) {
    return { ok: true, lead: (await response.json()) as Lead };
  }
  if (response.status === 422) {
    const body = (await response.json().catch(() => null)) as {
      detail?: unknown;
    } | null;
    return { ok: false, ...fieldErrorsFromDetail(body?.detail) };
  }
  return { ok: false, fieldErrors: {}, formError: GENERIC_ERROR };
}

/** Log in; the backend sets the httpOnly `alma_session` cookie on success. */
export async function login(
  email: string,
  password: string,
): Promise<{ ok: boolean; error?: string }> {
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (response.ok) return { ok: true };
    if (response.status === 401) {
      return { ok: false, error: "Invalid email or password." };
    }
    return { ok: false, error: GENERIC_ERROR };
  } catch {
    return { ok: false, error: GENERIC_ERROR };
  }
}

/** Log out; the backend clears the session cookie. Returns whether it succeeded. */
export async function logout(): Promise<{ ok: boolean }> {
  try {
    const response = await fetch("/api/auth/logout", { method: "POST" });
    return { ok: response.ok };
  } catch {
    return { ok: false };
  }
}

export type MarkReachedOutResult =
  { ok: true } | { ok: false; error: string; authExpired?: boolean };

/** Transition a lead to REACHED_OUT. */
export async function markReachedOut(
  id: string,
): Promise<MarkReachedOutResult> {
  try {
    const response = await fetch(`/api/leads/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: "REACHED_OUT" }),
    });
    if (response.ok) return { ok: true };
    if (response.status === 401) {
      // Session expired (cookie TTL is 8h) — the caller should send them to login.
      return {
        ok: false,
        authExpired: true,
        error: "Your session expired — please sign in again.",
      };
    }
    if (response.status === 409) {
      return {
        ok: false,
        error: "Lead was already updated — refresh to see the latest.",
      };
    }
    return { ok: false, error: "Could not update the lead. Please try again." };
  } catch {
    return { ok: false, error: "Could not update the lead. Please try again." };
  }
}

/** Server-side: list one page of leads, forwarding the caller's cookie header. */
export function fetchLeads(
  cookieHeader: string,
  state?: LeadState,
  limit?: number,
  offset?: number,
): Promise<Response> {
  const url = new URL("/api/leads", BACKEND_URL);
  if (state) url.searchParams.set("state", state);
  if (limit != null) url.searchParams.set("limit", String(limit));
  if (offset != null) url.searchParams.set("offset", String(offset));
  return fetch(url, { headers: { cookie: cookieHeader }, cache: "no-store" });
}

/** Server-side: check the current session, forwarding the cookie header. */
export function fetchMe(cookieHeader: string): Promise<Response> {
  return fetch(`${BACKEND_URL}/api/auth/me`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });
}
