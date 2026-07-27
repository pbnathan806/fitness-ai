import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/hooks/useAuth"
import { ROLE_LABELS } from "@/lib/constants"

/** Shared placeholder dashboard shell for all three roles. Real dashboard
 * data (see backend `/api/v1/dashboard/*`) is a business screen and out of
 * scope for this frontend-foundation task. */
export function DashboardHomePage() {
  const { session } = useAuth()
  if (!session?.activeRole) return null

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>
            Signed in as {ROLE_LABELS[session.activeRole]} · User ID {session.userId}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          This is the {ROLE_LABELS[session.activeRole]} dashboard shell. Metrics and widgets will be added in a
          future task.
        </CardContent>
      </Card>
    </div>
  )
}
