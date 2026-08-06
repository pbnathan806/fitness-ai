import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ClipboardCheck, ChevronRight, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { checkInService } from "@/services/checkInService"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"

type Tab = "pending" | "all"

function checkInSummary(mood: number | null, energyLevel: number | null): string {
  const moodText = mood != null ? `Mood ${mood}/5` : "Mood N/A"
  const energyText = energyLevel != null ? `Energy ${energyLevel}/5` : "Energy N/A"
  return `${moodText} · ${energyText}`
}

/** Trainer's own check-ins: a Pending queue (sessions started but no
 * check-in yet, mirrors SuperAdminCheckInsPage exactly, scoped to assigned
 * clients server-side) and an All log (every submitted check-in, newest
 * first). Submitting/editing a specific check-in already works via
 * SessionCheckInCard on the session details page - this page is just the
 * missing entry points into that existing capability. */
export function TrainerCheckInsPage() {
  const [tab, setTab] = useState<Tab>("pending")

  const pendingQuery = useQuery({
    queryKey: ["check-ins", "pending"],
    queryFn: checkInService.listPending,
    enabled: tab === "pending",
  })

  const allQuery = useQuery({
    queryKey: ["check-ins", "all"],
    queryFn: checkInService.listAllCheckIns,
    enabled: tab === "all",
  })

  const clientsQuery = useQuery({
    queryKey: ["clients", "all"],
    queryFn: clientService.listAllClients,
    enabled: tab === "all",
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const sortedCheckIns = useMemo(() => {
    return [...(allQuery.data ?? [])].sort(
      (a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime(),
    )
  }, [allQuery.data])

  const allIsLoading = allQuery.isLoading || clientsQuery.isLoading
  const allIsError = allQuery.isError

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Check-ins</h1>
        <p className="text-sm text-muted-foreground">Client wellness check-ins for your assigned clients.</p>
      </div>

      <div className="flex gap-2">
        <Button variant={tab === "pending" ? "default" : "outline"} size="sm" onClick={() => setTab("pending")}>
          Pending
        </Button>
        <Button variant={tab === "all" ? "default" : "outline"} size="sm" onClick={() => setTab("all")}>
          All
        </Button>
      </div>

      {tab === "pending" && (
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
              <ErrorState message={getApiErrorMessage(pendingQuery.error)} onRetry={() => pendingQuery.refetch()} />
            )}

            {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data?.length === 0 && (
              <EmptyState icon={ClipboardCheck} message="No pending check-ins. Everything is up to date." />
            )}

            {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data && pendingQuery.data.length > 0 && (
              <ul className="divide-y">
                {pendingQuery.data.map((item) => (
                  <li key={item.session_id}>
                    <Link
                      to={`/trainer/sessions/${item.session_id}`}
                      className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0 hover:bg-muted/50"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium">{item.client_name}</p>
                        <p className="text-xs text-muted-foreground">Scheduled {formatDateTime(item.scheduled_start)}</p>
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
      )}

      {tab === "all" && (
        <Card>
          <CardHeader>
            <CardTitle>All Check-ins</CardTitle>
            <CardDescription>Every check-in submitted for your assigned clients, newest first.</CardDescription>
          </CardHeader>
          <CardContent>
            {allIsLoading && (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            )}

            {!allIsLoading && allIsError && (
              <ErrorState message={getApiErrorMessage(allQuery.error, "Unable to load check-ins.")} onRetry={() => allQuery.refetch()} />
            )}

            {!allIsLoading && !allIsError && sortedCheckIns.length === 0 && (
              <EmptyState icon={ClipboardCheck} message="No check-ins found." />
            )}

            {!allIsLoading && !allIsError && sortedCheckIns.length > 0 && (
              <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Client</th>
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">Summary</th>
                      <th className="px-3 py-2 font-medium">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {sortedCheckIns.map((checkIn) => (
                      <tr key={checkIn.id} className="hover:bg-muted/30">
                        <td className="max-w-[180px] truncate px-3 py-2.5 font-medium">
                          {clientNameById.get(checkIn.client_id) ?? `Client #${checkIn.client_id.slice(0, 8)}`}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                          {formatDateTime(checkIn.submitted_at)}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {checkInSummary(checkIn.mood, checkIn.energy_level)}
                        </td>
                        <td className="px-3 py-2.5 text-right whitespace-nowrap">
                          <Button
                            variant="ghost"
                            size="sm"
                            render={<Link to={`/trainer/sessions/${checkIn.session_id}`} />}
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
      )}
    </div>
  )
}
