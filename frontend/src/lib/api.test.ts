import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createLead,
  fieldErrorsFromDetail,
  login,
  logout,
  markReachedOut,
} from "./api";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubFetch(result: Response | Error) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      result instanceof Error
        ? Promise.reject(result)
        : Promise.resolve(result),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fieldErrorsFromDetail", () => {
  it("maps detail entries onto known form fields by loc", () => {
    const { fieldErrors, formError } = fieldErrorsFromDetail([
      {
        loc: ["body", "email"],
        msg: "value is not a valid email address",
        type: "value_error",
      },
      {
        loc: ["body", "first_name"],
        msg: "String should have at least 1 character",
        type: "string_too_short",
      },
    ]);
    expect(fieldErrors).toEqual({
      email: "value is not a valid email address",
      first_name: "String should have at least 1 character",
    });
    expect(formError).toBeUndefined();
  });

  it("keeps the first message when a field has multiple errors", () => {
    const { fieldErrors } = fieldErrorsFromDetail([
      { loc: ["body", "resume"], msg: "first" },
      { loc: ["body", "resume"], msg: "second" },
    ]);
    expect(fieldErrors.resume).toBe("first");
  });

  it("falls back to a form error for unknown locs", () => {
    const { fieldErrors, formError } = fieldErrorsFromDetail([
      { loc: ["body", "mystery_field"], msg: "nope" },
    ]);
    expect(fieldErrors).toEqual({});
    expect(formError).toBeTruthy();
  });

  it("falls back to a form error for malformed payloads", () => {
    expect(fieldErrorsFromDetail("Internal error").formError).toBeTruthy();
    expect(fieldErrorsFromDetail(undefined).formError).toBeTruthy();
    expect(fieldErrorsFromDetail([{ msg: "no loc" }]).formError).toBeTruthy();
  });
});

describe("createLead", () => {
  it("returns the lead on 201", async () => {
    const lead = {
      id: "1",
      first_name: "Jane",
      last_name: "Doe",
      email: "jane@example.com",
      state: "PENDING",
      resume_filename: "resume.pdf",
      created_at: "2026-07-07T00:00:00Z",
      updated_at: "2026-07-07T00:00:00Z",
    };
    stubFetch(jsonResponse(201, lead));
    expect(await createLead(new FormData())).toEqual({ ok: true, lead });
  });

  it("maps a 422 detail onto field errors", async () => {
    stubFetch(
      jsonResponse(422, {
        detail: [{ loc: ["body", "email"], msg: "bad email" }],
      }),
    );
    expect(await createLead(new FormData())).toMatchObject({
      ok: false,
      fieldErrors: { email: "bad email" },
    });
  });

  it("returns a form error on network failure", async () => {
    stubFetch(new Error("network"));
    const result = await createLead(new FormData());
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.formError).toBeTruthy();
  });
});

describe("login", () => {
  it("succeeds on 200", async () => {
    stubFetch(jsonResponse(200, { email: "attorney@example.com" }));
    expect(await login("a@b.co", "pw")).toEqual({ ok: true });
  });

  it("reports invalid credentials on 401", async () => {
    stubFetch(jsonResponse(401, { detail: "nope" }));
    const result = await login("a@b.co", "pw");
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/invalid/i);
  });
});

describe("logout", () => {
  it("is ok on 204", async () => {
    stubFetch(new Response(null, { status: 204 }));
    expect(await logout()).toEqual({ ok: true });
  });

  it("is not ok on network failure", async () => {
    stubFetch(new Error("down"));
    expect(await logout()).toEqual({ ok: false });
  });
});

describe("markReachedOut", () => {
  it("returns ok on 200", async () => {
    stubFetch(jsonResponse(200, {}));
    expect(await markReachedOut("id")).toEqual({ ok: true });
  });

  it("flags an expired session on 401", async () => {
    stubFetch(jsonResponse(401, { detail: "x" }));
    expect(await markReachedOut("id")).toMatchObject({
      ok: false,
      authExpired: true,
    });
  });

  it("returns a conflict message on 409 without flagging auth", async () => {
    stubFetch(jsonResponse(409, {}));
    const result = await markReachedOut("id");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toMatch(/already updated/i);
      expect(result.authExpired).toBeUndefined();
    }
  });

  it("returns a generic error on 500", async () => {
    stubFetch(jsonResponse(500, {}));
    expect((await markReachedOut("id")).ok).toBe(false);
  });
});
