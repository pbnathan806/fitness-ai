import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ClipboardCheck, ChevronRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { checkInService } from "@/services/checkInService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"

/** Oversight view of every Session missing a Check-in (Session not
 * CANCELLED, already started, no Check-in yet - see backend
 * CheckInService.list_pending_check_ins). SUPER_ADMIN sees every client;
 * TRAINER (own placeholder nav item) would see only assigned clients, but
 * this screen itself is SUPER_ADMIN-only per Task Check-ins V2 Module 7. */
export function SuperAdminCheckInsPage() {
  const pendingQuery = useQuery({
    queryKey: ["check-ins", "pending"],
    queryFn: checkInService.listPending,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Check-ins</h1>
        <p className="text-sm text-muted-foreground">
          Sessions that have started but have no check-in on file yet.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>Pending Check-ins</CardTitle>
            {!pendingQuery.isLoading && !pendingQuery.isError && (
              <Badge variant={pendingQuery.data && pendingQuery.data.length > 0 ? "warning" : "secondary"}>
                {pendingQuery.data?.length ?? 0} pending
              </Badge>
            )}
          </div>
          <CardDescription>Click a row to open the session and view or edit its check-in.</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingQuery.isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!pendingQuery.isLoading && pendingQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(pendingQuery.error)}
              onRetry={() => pendingQuery.refetch()}
            />
          )}

          {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data?.length === 0 && (
            <EmptyState icon={ClipboardCheck} message="No pending check-ins. Everything is up to date." />
          )}

          {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data && pendingQuery.data.length > 0 && (
            <ul className="divide-y">
              {pendingQuery.data.map((item) => (
                <li key={item.session_id}>
                  <Link
                    to={`/super-admin/sessions/${item.session_id}`}
                    className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0 hover:bg-muted/50"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{item.client_name}</p>
                      <p className="text-xs text-muted-foreground">
                        Scheduled {formatDateTime(item.scheduled_start)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="warning">
                        {item.days_pending} day{item.days_pending === 1 ? "" : "s"} pending
                      </Badge>
                      <ChevronRight className="size-4 text-muted-foreground" aria-hidden="true" />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
