import fc from "fast-check";
import { describe, expect, it } from "vitest";

import { fieldErrorsFromDetail } from "./api";

// Mirrors LEAD_FORM_FIELDS in api.ts — the only keys that may ever appear.
const KNOWN_FIELDS = ["first_name", "last_name", "email", "resume"];

// `fieldErrorsFromDetail` parses a FastAPI 422 `detail`, which is attacker-
// influenced JSON (`response.json()`), so it must be total: no input may throw,
// and the result shape must always be safe to render.
describe("fieldErrorsFromDetail (property-based)", () => {
  it("is total and well-formed for absolutely any input", () => {
    fc.assert(
      fc.property(fc.anything(), (detail) => {
        const { fieldErrors, formError } = fieldErrorsFromDetail(detail);

        // Only known fields, and every value is a renderable string.
        for (const [key, value] of Object.entries(fieldErrors)) {
          expect(KNOWN_FIELDS).toContain(key);
          expect(typeof value).toBe("string");
        }
        if (formError !== undefined) expect(typeof formError).toBe("string");

        // The form never fails silently: there is always something to show the
        // user — a field error, a form-level error, or both.
        const hasFieldError = Object.keys(fieldErrors).length > 0;
        expect(hasFieldError || Boolean(formError)).toBe(true);
      }),
    );
  });

  it("maps a well-formed FastAPI entry onto its field", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...KNOWN_FIELDS),
        fc.string({ minLength: 1 }),
        (field, msg) => {
          const { fieldErrors, formError } = fieldErrorsFromDetail([
            { loc: ["body", field], msg },
          ]);
          expect(fieldErrors).toEqual({ [field]: msg });
          expect(formError).toBeUndefined();
        },
      ),
    );
  });

  it("keeps the first message when the same field errors twice", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...KNOWN_FIELDS),
        fc.string({ minLength: 1 }),
        fc.string({ minLength: 1 }),
        (field, first, second) => {
          const { fieldErrors } = fieldErrorsFromDetail([
            { loc: ["body", field], msg: first },
            { loc: ["body", field], msg: second },
          ]);
          expect(fieldErrors[field as keyof typeof fieldErrors]).toBe(first);
        },
      ),
    );
  });

  it("falls back to a form error when no entry names a known field", () => {
    const notAField = fc.string().filter((s) => !KNOWN_FIELDS.includes(s));
    fc.assert(
      fc.property(
        fc.array(fc.record({ loc: fc.array(notAField), msg: fc.string() })),
        (detail) => {
          const { fieldErrors, formError } = fieldErrorsFromDetail(detail);
          expect(fieldErrors).toEqual({});
          expect(formError).toBeTruthy();
        },
      ),
    );
  });

  it("never loses a valid field error amid arbitrary junk entries", () => {
    fc.assert(
      fc.property(
        fc.array(fc.anything()),
        fc.constantFrom(...KNOWN_FIELDS),
        fc.string({ minLength: 1 }),
        fc.array(fc.anything()),
        (before, field, msg, after) => {
          const detail = [...before, { loc: ["body", field], msg }, ...after];
          const { fieldErrors } = fieldErrorsFromDetail(detail);
          // Surrounding garbage can never drop a genuine field error.
          expect(field in fieldErrors).toBe(true);
          expect(typeof fieldErrors[field as keyof typeof fieldErrors]).toBe(
            "string",
          );
        },
      ),
    );
  });
});
