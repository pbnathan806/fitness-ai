/** Renders an ISO timestamp in the viewer's own local timezone (so it reads
 * correctly for both US and IST users per TIMEZONE_REQUIREMENTS.md) with the
 * zone abbreviation shown for clarity. */
export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso))
}

/** Renders an ISO date/timestamp as a date-only string in the viewer's own
 * local timezone (dates alone have no timezone, but a `datetime` input may). */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(iso))
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
