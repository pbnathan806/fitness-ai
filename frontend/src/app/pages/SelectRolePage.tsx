import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/common/ErrorState"
import { useAuth } from "@/hooks/useAuth"
import { getApiErrorMessage } from "@/lib/errors"
import { ROLE_HOME_PATH, ROLE_LABELS, type RoleName } from "@/lib/constants"

export function SelectRolePage() {
  const { session, needsRoleSelection, selectRole } = useAuth()
  const navigate = useNavigate()
  const [pendingRole, setPendingRole] = useState<RoleName | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (!needsRoleSelection) {
    return <Navigate to="/" replace />
  }

  const handleSelect = async (role: RoleName) => {
    setPendingRole(role)
    setError(null)
    try {
      await selectRole(role)
      navigate(ROLE_HOME_PATH[role], { replace: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setPendingRole(null)
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Choose a role</CardTitle>
          <CardDescription>Your account has access to more than one role.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {error && <ErrorState message={error} />}
          {session.roles.map((role) => (
            <Button
              key={role}
              variant="outline"
              className="w-full justify-start"
              disabled={pendingRole !== null}
              onClick={() => handleSelect(role)}
            >
              {pendingRole === role ? "Continuing..." : ROLE_LABELS[role]}
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
