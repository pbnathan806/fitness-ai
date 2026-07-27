import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import { flushSync } from "react-dom"
import { authService } from "@/services/authService"
import { setUnauthorizedHandler } from "@/services/apiClient"
import { clearStoredSession, readStoredSession, writeStoredSession } from "@/lib/storage"
import type { RoleName } from "@/lib/constants"
import type { AuthSession } from "@/types/auth"

interface AuthContextValue {
  session: AuthSession | null
  /** True until the initial session-restore-from-storage check has run. */
  isInitializing: boolean
  isAuthenticated: boolean
  /** Roles requiring selection before the session has an `activeRole`. */
  needsRoleSelection: boolean
  login: (email: string, password: string) => Promise<void>
  selectRole: (role: RoleName) => Promise<void>
  logout: () => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | null>(null)

function isSessionExpired(session: AuthSession): boolean {
  return Date.now() >= session.expiresAt
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const stored = readStoredSession()
    if (stored && !isSessionExpired(stored)) {
      setSession(stored)
    } else if (stored) {
      clearStoredSession()
    }
    setIsInitializing(false)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setSession(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await authService.login({ email, password })

    let nextSession: AuthSession = {
      accessToken: response.access_token,
      tokenType: response.token_type,
      expiresAt: Date.now() + response.expires_in * 1000,
      userId: response.user_id,
      roles: response.roles,
      activeRole: null,
    }

    // Persist immediately: `switchRole` below issues an authenticated request,
    // and the apiClient interceptor attaches the Authorization header by
    // reading the token from storage, not from in-memory state.
    writeStoredSession(nextSession)

    if (response.roles.length === 1) {
      const switched = await authService.switchRole(response.roles[0])
      nextSession = {
        ...nextSession,
        accessToken: switched.access_token,
        tokenType: switched.token_type,
        expiresAt: Date.now() + switched.expires_in * 1000,
        activeRole: switched.active_role,
      }
      writeStoredSession(nextSession)
    }
    // Callers immediately `navigate()` once this promise resolves (e.g. to a
    // role-restricted route) - flushSync guarantees ProtectedRoute sees the
    // new session on that very next render instead of a stale one.
    flushSync(() => setSession(nextSession))
  }, [])

  const selectRole = useCallback(async (role: RoleName) => {
    const switched = await authService.switchRole(role)
    flushSync(() => {
      setSession((current) => {
        if (!current) return current
        const nextSession: AuthSession = {
          ...current,
          accessToken: switched.access_token,
          tokenType: switched.token_type,
          expiresAt: Date.now() + switched.expires_in * 1000,
          activeRole: switched.active_role,
        }
        writeStoredSession(nextSession)
        return nextSession
      })
    })
  }, [])

  const logout = useCallback(() => {
    clearStoredSession()
    setSession(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      isInitializing,
      isAuthenticated: session !== null,
      needsRoleSelection: session !== null && session.activeRole === null,
      login,
      selectRole,
      logout,
    }),
    [session, isInitializing, login, selectRole, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
