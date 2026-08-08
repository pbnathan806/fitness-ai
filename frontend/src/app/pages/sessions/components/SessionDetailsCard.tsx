import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDisplayTimezone } from "@/lib/displayTimezone"
import { formatDateTime } from "@/lib/format"
import { SESSION_STATUS_BADGE_VARIANT, SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import {
  SESSION_ATTENDANCE_STATUS_BADGE_VARIANT,
  SESSION_ATTENDANCE_STATUS_LABELS,
} from "@/lib/sessionAttendanceStatus"
import type { Session } from "@/types/session"

interface SessionDetailsCardProps {
  session: Session
  clientName: string
  trainerName: string
}

/** Full-detail read-only view (Task 22.6 requirement 2) - used by the
 * SUPER_ADMIN and TRAINER session details screens, which are both permitted
 * to see trainer_notes/trainer_feedback/next_session_focus. The Client "My
 * Sessions" details screen uses ClientSessionDetailsCard instead, which is
 * typed to a narrower view that cannot carry those fields. */
export function SessionDetailsCard({ session, clientName, trainerName }: SessionDetailsCardProps) {
  const timezone = useDisplayTimezone()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Session Details</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="text-xs text-muted-foreground">Client</p>
          <p className="text-sm font-medium">{clientName}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Trainer</p>
          <p className="text-sm font-medium">{trainerName}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Scheduled Start</p>
          <p className="text-sm font-medium">{formatDateTime(session.scheduled_start, timezone)}</p>
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
          <p className="text-xs text-muted-foreground">Trainer Notes</p>
          <p className="text-sm font-medium whitespace-pre-wrap">{session.trainer_notes || "—"}</p>
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <p className="text-xs text-muted-foreground">Trainer Feedback</p>
          <p className="text-sm font-medium whitespace-pre-wrap">{session.trainer_feedback || "—"}</p>
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <p className="text-xs text-muted-foreground">Homework</p>
          <p className="text-sm font-medium whitespace-pre-wrap">{session.homework || "—"}</p>
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <p className="text-xs text-muted-foreground">Next Session Focus</p>
          <p className="text-sm font-medium whitespace-pre-wrap">{session.next_session_focus || "—"}</p>
        </div>
      </CardContent>
    </Card>
  )
}
