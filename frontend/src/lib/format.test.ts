import { describe, expect, it } from "vitest";

import { formatDateTime, parseUtcDate } from "./format";

describe("parseUtcDate", () => {
  it("treats naive ISO timestamps as UTC", () => {
    expect(parseUtcDate("2026-07-07T15:30:00").toISOString()).toBe(
      "2026-07-07T15:30:00.000Z",
    );
  });

  it("respects an explicit timezone suffix", () => {
    expect(parseUtcDate("2026-07-07T15:30:00Z").toISOString()).toBe(
      "2026-07-07T15:30:00.000Z",
    );
    expect(parseUtcDate("2026-07-07T15:30:00+02:00").toISOString()).toBe(
      "2026-07-07T13:30:00.000Z",
    );
  });
});

describe("formatDateTime", () => {
  it("renders a readable date and time", () => {
    // Intl may use a narrow no-break space before AM/PM — normalize it.
    const formatted = formatDateTime("2026-07-07T15:30:00", "UTC").replace(
      / /g,
      " ",
    );
    expect(formatted).toBe("Jul 7, 2026, 3:30 PM");
  });
});
