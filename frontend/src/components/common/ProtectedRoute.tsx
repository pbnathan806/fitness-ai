import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { FullPageSpinner } from "@/components/common/LoadingSpinner"
import type { RoleName } from "@/lib/constants"

interface ProtectedRouteProps {
  allowedRoles?: RoleName[]
}

/** Gate for authenticated (and optionally role-restricted) routes.
 * Unauthenticated -> /login. Authenticated but no role chosen yet -> /select-role.
 * Authenticated with a role outside `allowedRoles` -> /unauthorized. */
export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isInitializing, needsRoleSelection, session } = useAuth()
  const location = useLocation()

  if (isInitializing) {
    return <FullPageSpinner label="Checking your session..." />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (needsRoleSelection) {
    return <Navigate to="/select-role" replace />
  }

  if (allowedRoles && session?.activeRole && !allowedRoles.includes(session.activeRole)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <Outlet />
}
