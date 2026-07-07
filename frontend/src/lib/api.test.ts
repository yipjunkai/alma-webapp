import { describe, expect, it } from "vitest";

import { fieldErrorsFromDetail } from "./api";

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
