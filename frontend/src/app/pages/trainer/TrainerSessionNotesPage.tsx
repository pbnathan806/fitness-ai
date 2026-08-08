import { useMemo } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ClipboardList, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { sessionService } from "@/services/sessionService"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"
import { useDisplayTimezone } from "@/lib/displayTimezone"
import { formatDateTime } from "@/lib/format"

const PREVIEW_MAX_LENGTH = 80

function notesPreview(notes: string | null): string {
  if (!notes || !notes.trim()) return "No notes yet"
  const trimmed = notes.trim()
  return trimmed.length > PREVIEW_MAX_LENGTH ? `${trimmed.slice(0, PREVIEW_MAX_LENGTH)}…` : trimmed
}

/** Browsable log of the trainer's own sessions with a trainer_notes preview,
 * newest first. Editing notes happens on the existing session details page
 * (`/trainer/sessions/:id`, SessionNotesForm) - this page is just the
 * missing entry point into that already-working capability. */
export function TrainerSessionNotesPage() {
  const timezone = useDisplayTimezone()
  const sessionsQuery = useQuery({ queryKey: ["sessions", "all"], queryFn: sessionService.listAllSessions })
  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const sortedSessions = useMemo(() => {
    return [...(sessionsQuery.data ?? [])].sort(
      (a, b) => new Date(b.scheduled_start).getTime() - new Date(a.scheduled_start).getTime(),
    )
  }, [sessionsQuery.data])

  const isLoading = sessionsQuery.isLoading || clientsQuery.isLoading
  const isError = sessionsQuery.isError

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Session Notes</h1>
        <p className="text-sm text-muted-foreground">
          Browse notes recorded across all your sessions.
          {timezone && ` Times shown in your profile timezone (${timezone}).`}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="size-4 text-muted-foreground" aria-hidden="true" />
            Session Notes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!isLoading && isError && (
            <ErrorState
              message={getApiErrorMessage(sessionsQuery.error, "Unable to load sessions.")}
              onRetry={() => sessionsQuery.refetch()}
            />
          )}

          {!isLoading && !isError && sortedSessions.length === 0 && (
            <EmptyState icon={ClipboardList} message="No sessions found." />
          )}

          {!isLoading && !isError && sortedSessions.length > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Client</th>
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Notes Preview</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {sortedSessions.map((session) => (
                    <tr key={session.id} className="hover:bg-muted/30">
                      <td className="max-w-[180px] truncate px-3 py-2.5 font-medium">
                        {clientNameById.get(session.client_id) ?? `Client #${session.client_id.slice(0, 8)}`}
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                        {formatDateTime(session.scheduled_start, timezone)}
                      </td>
                      <td className="max-w-[360px] px-3 py-2.5 text-muted-foreground">
                        <span className={session.trainer_notes?.trim() ? "" : "italic"}>
                          {notesPreview(session.trainer_notes)}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          render={<Link to={`/trainer/sessions/${session.id}`} />}
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
