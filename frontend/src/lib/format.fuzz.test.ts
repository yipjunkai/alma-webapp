import fc from "fast-check";
import { describe, expect, it } from "vitest";

import { formatDateTime, parseUtcDate } from "./format";

// Real timestamps only: fc.date() otherwise also yields `new Date(NaN)`, whose
// toISOString() throws — out of scope for these valid-timestamp properties.
const IN_RANGE = {
  min: new Date("1900-01-01T00:00:00Z"),
  max: new Date("2200-01-01T00:00:00Z"),
  noInvalidDate: true,
};

describe("parseUtcDate (property-based)", () => {
  it("round-trips any Date through its ISO string", () => {
    // toISOString() always carries a `Z`, so the instant must survive exactly.
    fc.assert(
      fc.property(fc.date(IN_RANGE), (d) => {
        expect(parseUtcDate(d.toISOString()).getTime()).toBe(d.getTime());
      }),
    );
  });

  it("interprets a timezone-less ISO timestamp as UTC", () => {
    const pad = (n: number, len = 2) => String(n).padStart(len, "0");
    fc.assert(
      fc.property(
        fc.integer({ min: 1970, max: 2999 }),
        fc.integer({ min: 1, max: 12 }),
        fc.integer({ min: 1, max: 28 }), // ≤28 sidesteps month-length edge cases
        fc.integer({ min: 0, max: 23 }),
        fc.integer({ min: 0, max: 59 }),
        fc.integer({ min: 0, max: 59 }),
        (year, month, day, hour, min, sec) => {
          const naive = `${pad(year, 4)}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(min)}:${pad(sec)}`;
          expect(parseUtcDate(naive).getTime()).toBe(
            Date.UTC(year, month - 1, day, hour, min, sec),
          );
        },
      ),
    );
  });
});

describe("formatDateTime (property-based)", () => {
  it("never throws, whatever string it is handed", () => {
    fc.assert(
      fc.property(fc.string(), (s) => {
        expect(() => formatDateTime(s, "UTC")).not.toThrow();
      }),
    );
  });

  it("renders every real timestamp as a non-empty, valid string", () => {
    fc.assert(
      fc.property(fc.date(IN_RANGE), (d) => {
        const out = formatDateTime(d.toISOString(), "UTC");
        expect(out.length).toBeGreaterThan(0);
        expect(out).not.toBe("Invalid Date");
      }),
    );
  });
});
