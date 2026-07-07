/**
 * Parse an ISO timestamp from the backend. The API stores UTC but may omit
 * the `Z` suffix; without it, `new Date()` would parse as local time.
 */
export function parseUtcDate(iso: string): Date {
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasTimezone ? iso : `${iso}Z`);
}

/**
 * Human-readable timestamp, e.g. "Jul 7, 2026, 3:30 PM".
 * `timeZone` is overridable for deterministic tests; defaults to server-local.
 */
export function formatDateTime(iso: string, timeZone?: string): string {
  const date = parseUtcDate(iso);
  // `Intl.DateTimeFormat.format` throws on an invalid Date, so a malformed
  // timestamp would crash rendering. Fall back to the raw value instead.
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone,
  }).format(date);
}
