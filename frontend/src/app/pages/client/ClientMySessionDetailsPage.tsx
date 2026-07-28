import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import { SESSION_STATUS_BADGE_VARIANT, SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import {
  SESSION_ATTENDANCE_STATUS_BADGE_VARIANT,
  SESSION_ATTENDANCE_STATUS_LABELS,
} from "@/lib/sessionAttendanceStatus"

/** Client "My Sessions" details (Task 22.6 requirement 8) - read-only, and
 * fetched via sessionService.getMySessionDetail, which narrows the response
 * to ClientSessionView. trainer_notes, trainer_feedback, and
 * next_session_focus are typed out of this screen entirely, not merely
 * hidden in the UI. Trainer identity is intentionally not resolved to a name
 * here: `GET /trainers/{id}` is not permitted for the CLIENT role, and Task
 * 22.6 scopes this screen to session APIs only. */
export function ClientMySessionDetailsPage() {
  const { id } = useParams<{ id: string }>()

  const sessionQuery = useQuery({
    queryKey: ["sessions", "my-sessions", id],
    queryFn: () => sessionService.getMySessionDetail(id!),
    enabled: !!id,
  })

  if (sessionQuery.isLoading) {
    return <LoadingSpinner label="Loading session..." className="py-16" />
  }

  if (sessionQuery.isError || !sessionQuery.data) {
    return (
      <ErrorState
        title="Unable to load session"
        message={getApiErrorMessage(sessionQuery.error, "This session could not be found.")}
        onRetry={() => sessionQuery.refetch()}
      />
    )
  }

  const session = sessionQuery.data

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/client/my-sessions" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to my sessions
      </Button>

      <div>
        <h1 className="text-xl font-semibold">{formatDateTime(session.scheduled_start)}</h1>
        <p className="text-sm text-muted-foreground">Session details</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Session Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Scheduled Start</p>
            <p className="text-sm font-medium">{formatDateTime(session.scheduled_start)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Duration</p>
            <p className="text-sm font-medium">{session.duration_minutes} minutes</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Meeting Type</p>
            <p className="text-sm font-medium">{SESSION_MEETING_TYPE_LABELS[session.meeting_type]}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Meeting Link</p>
            {session.meeting_link ? (
              <a
                href={session.meeting_link}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium text-primary hover:underline"
              >
                {session.meeting_link}
              </a>
            ) : (
              <p className="text-sm font-medium">—</p>
            )}
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Status</p>
            <Badge variant={SESSION_STATUS_BADGE_VARIANT[session.status]} className="mt-0.5">
              {SESSION_STATUS_LABELS[session.status]}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Attendance</p>
            <Badge variant={SESSION_ATTENDANCE_STATUS_BADGE_VARIANT[session.attendance_status ?? "NOT_RECORDED"]} className="mt-0.5">
              {SESSION_ATTENDANCE_STATUS_LABELS[session.attendance_status ?? "NOT_RECORDED"]}
            </Badge>
          </div>
          <div className="sm:col-span-2 lg:col-span-3">
            <p className="text-xs text-muted-foreground">Homework</p>
            <p className="text-sm font-medium whitespace-pre-wrap">{session.homework || "—"}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
