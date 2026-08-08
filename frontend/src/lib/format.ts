/** Renders an ISO timestamp. Defaults to the viewer's own local timezone (so
 * it reads correctly for both US and IST users per TIMEZONE_REQUIREMENTS.md);
 * pass `timezone` (an IANA identifier) to render in a specific timezone
 * instead - used on Trainer-facing screens to show times in the trainer's
 * own profile timezone rather than the browser's, via useDisplayTimezone(). */
export function formatDateTime(iso: string, timezone?: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    ...(timezone ? { timeZone: timezone } : {}),
  }).format(new Date(iso))
}

/** Renders an ISO date/timestamp as a date-only string. Defaults to the
 * viewer's own local timezone; pass `timezone` to render in a specific
 * timezone instead. Only pass `timezone` for values with a real time
 * component (a full datetime) - a date-only value (e.g. "2026-08-08") has no
 * timezone of its own, and applying one can shift it to the wrong day. */
export function formatDate(iso: string, timezone?: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    ...(timezone ? { timeZone: timezone } : {}),
  }).format(new Date(iso))
}

export function formatRelativeToNow(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const diffMinutes = Math.round(diffMs / 60_000)

  if (diffMinutes < 1) return "just now"
  if (diffMinutes < 60) return `${diffMinutes}m ago`

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.round(diffHours / 24)
  return `${diffDays}d ago`
}
