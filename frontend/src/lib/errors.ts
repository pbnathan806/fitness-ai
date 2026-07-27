import { isAxiosError } from "axios"

/** FastAPI returns validation/business errors as `{ detail: string | object }`. */
export function getApiErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string") return detail

    // No response at all (real network/CORS/DNS failure), or a gateway/server
    // error with no FastAPI `detail` body - e.g. the Vite dev proxy answers
    // with a plain-text 502 (not JSON) when the backend process is down. Both
    // mean "the server, not your input" - never let this fall through to a
    // caller-supplied fallback like "Invalid email or password.".
    const status = error.response?.status
    if (!error.response || (status !== undefined && status >= 500)) {
      return "Unable to reach the server. Please check your connection."
    }
  }

  return fallback
}
