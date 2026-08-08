import { Link } from "react-router-dom"
import { ClipboardList } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { formatDateTime } from "@/lib/format"
import type { SessionNotesGapSession } from "@/types/trainer"

interface SessionNotesGapWidgetProps {
  gapDays: number | undefined
  timezone: string | undefined
  sessions: SessionNotesGapSession[] | undefined
  clientNameById: Map<string, string>
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

export function SessionNotesGapWidget({
  gapDays,
  timezone,
  sessions,
  clientNameById,
  isLoading,
  isError,
  onRetry,
}: SessionNotesGapWidgetProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="size-4 text-muted-foreground" aria-hidden="true" />
          Session Notes Gap
        </CardTitle>
        <CardDescription>
          {gapDays === undefined
            ? "Past sessions missing notes."
            : `Past sessions from the last ${gapDays} day${gapDays === 1 ? "" : "s"} that are missing notes.`}
          {timezone && ` Times shown in your profile timezone (${timezone}).`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && (
          <ErrorState message="Couldn't load session notes gap." onRetry={onRetry} />
        )}

        {!isLoading && !isError && (sessions?.length ?? 0) === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No missing notes in this window.
          </p>
        )}

        {!isLoading && !isError && sessions && sessions.length > 0 && (
          <ul className="divide-y">
            {sessions.map((session) => (
              <li key={session.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {clientNameById.get(session.client_id) ?? "Client"}
                  </p>
                  <p className="text-xs text-muted-foreground">{formatDateTime(session.scheduled_start, timezone)}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  render={<Link to={`/trainer/sessions/${session.id}`} />}
                  nativeButton={false}
                >
                  Add Notes
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
