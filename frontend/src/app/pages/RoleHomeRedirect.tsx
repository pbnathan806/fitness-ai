import { Navigate } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
import { ROLE_HOME_PATH } from "@/lib/constants"

/** `/` always redirects to the signed-in user's active-role dashboard. */
export function RoleHomeRedirect() {
  const { session } = useAuth()
  if (!session?.activeRole) return null
  return <Navigate to={ROLE_HOME_PATH[session.activeRole]} replace />
}
