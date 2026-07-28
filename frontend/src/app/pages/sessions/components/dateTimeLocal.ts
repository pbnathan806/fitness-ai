/** `<input type="datetime-local">` has no timezone of its own - the browser
 * treats the value as wall-clock time in the viewer's local zone. Converting
 * through `Date` therefore correctly produces a timezone-aware UTC ISO
 * string for the API (required by `SessionCreateRequest.scheduled_start`)
 * while keeping the input showing the viewer's own local time, which is
 * what TIMEZONE_REQUIREMENTS.md calls for regardless of whether the viewer
 * is in a US zone or IST. */
export function toDateTimeLocalValue(iso: string): string {
  const date = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function fromDateTimeLocalValue(value: string): string {
  return new Date(value).toISOString()
}

/** Local (viewer-timezone) calendar date of an ISO timestamp, as "YYYY-MM-DD"
 * - matches the granularity of an `<input type="date">` Date filter. */
export function toLocalDateValue(iso: string): string {
  const date = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
