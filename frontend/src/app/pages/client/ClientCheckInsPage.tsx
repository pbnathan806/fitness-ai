import { useMemo } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ClipboardCheck, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { checkInService } from "@/services/checkInService"
import { useAuth } from "@/hooks/useAuth"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"

function checkInSummary(mood: number | null, energyLevel: number | null): string {
  const moodText = mood != null ? `Mood ${mood}/5` : "Mood N/A"
  const energyText = energyLevel != null ? `Energy ${energyLevel}/5` : "Energy N/A"
  return `${moodText} · ${energyText}`
}

/** Client's own check-in history - every check-in submitted for their
 * sessions, newest first, regardless of who filled it in. Check-ins are
 * primarily logged by the trainer during a session; the client can view
 * them here and optionally add/edit one themselves via the session details
 * page (SessionCheckInCard). Deliberately not framed as "pending" or
 * "missed" - check-ins are not mandated for clients to fill (see
 * project_checkins_v2_rbac_and_ui memory: clients get no pending queue). */
export function ClientCheckInsPage() {
  const { session } = useAuth()

  const checkInsQuery = useQuery({
    queryKey: ["check-ins", "all"],
    queryFn: checkInService.listAllCheckIns,
  })

  const sortedCheckIns = useMemo(() => {
    return [...(checkInsQuery.data ?? [])].sort(
      (a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime(),
    )
  }, [checkInsQuery.data])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Check-ins</h1>
        <p className="text-sm text-muted-foreground">
          Your check-in history. Your trainer usually logs these during a session, but you can add or edit one from
          any session's details page.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Check-in History</CardTitle>
          <CardDescription>Every check-in submitted for your sessions, newest first.</CardDescription>
        </CardHeader>
        <CardContent>
          {checkInsQuery.isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!checkInsQuery.isLoading && checkInsQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(checkInsQuery.error, "Unable to load check-ins.")}
              onRetry={() => checkInsQuery.refetch()}
            />
          )}

          {!checkInsQuery.isLoading && !checkInsQuery.isError && sortedCheckIns.length === 0 && (
            <EmptyState
              icon={ClipboardCheck}
              message="No check-ins yet. Your trainer can log one during your next session, or you can add one yourself from a session's details page."
            />
          )}

          {!checkInsQuery.isLoading && !checkInsQuery.isError && sortedCheckIns.length > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Summary</th>
                    <th className="px-3 py-2 font-medium">Submitted By</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {sortedCheckIns.map((checkIn) => (
                    <tr key={checkIn.id} className="hover:bg-muted/30">
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                        {formatDateTime(checkIn.submitted_at)}
                      </td>
                      <td className="px-3 py-2.5 text-muted-foreground">
                        {checkInSummary(checkIn.mood, checkIn.energy_level)}
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                        {checkIn.submitted_by === session?.userId ? "You" : "Trainer"}
                      </td>
                      <td className="px-3 py-2.5 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          render={<Link to={`/client/my-sessions/${checkIn.session_id}`} />}
                          nativeButton={false}
                        >
                          <Eye className="size-4" />
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
