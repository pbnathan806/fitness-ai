import { AUTH_STORAGE_KEY } from "@/lib/constants"
import type { AuthSession } from "@/types/auth"

export function readStoredSession(): AuthSession | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw) as AuthSession
    if (!parsed.accessToken || !parsed.userId) return null
    return parsed
  } catch {
    return null
  }
}

export function writeStoredSession(session: AuthSession): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}
