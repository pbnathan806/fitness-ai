import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { CalendarDays, ChevronLeft, ChevronRight, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { SessionFilters } from "@/app/pages/sessions/components/SessionFilters"
import { toLocalDateValue } from "@/app/pages/sessions/components/dateTimeLocal"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import { SESSION_STATUS_BADGE_VARIANT, SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import {
  SESSION_ATTENDANCE_STATUS_BADGE_VARIANT,
  SESSION_ATTENDANCE_STATUS_LABELS,
} from "@/lib/sessionAttendanceStatus"
import type { SessionMeetingType, SessionStatus } from "@/types/session"

const PAGE_SIZE = 10

/** Client "My Sessions" list (Task 22.6 requirement 8). Uses `GET
 * /sessions/my-sessions` only (via sessionService.getMySessions, which
 * already narrows the response to ClientSessionView) - trainer_notes,
 * trainer_feedback, and next_session_focus never reach this component. */
export function ClientMySessionsListPage() {
  const [statusFilter, setStatusFilter] = useState<SessionStatus | "ALL">("ALL")
  const [meetingTypeFilter, setMeetingTypeFilter] = useState<SessionMeetingType | "ALL">("ALL")
  const [dateFilter, setDateFilter] = useState("")
  const [page, setPage] = useState(1)

  const sessionsQuery = useQuery({ queryKey: ["sessions", "my-sessions"], queryFn: sessionService.getMySessions })

  const filteredSessions = useMemo(() => {
    return (sessionsQuery.data ?? [])
      .filter((s) => statusFilter === "ALL" || s.status === statusFilter)
      .filter((s) => meetingTypeFilter === "ALL" || s.meeting_type === meetingTypeFilter)
      .filter((s) => !dateFilter || toLocalDateValue(s.scheduled_start) === dateFilter)
  }, [sessionsQuery.data, statusFilter, meetingTypeFilter, dateFilter])

  const totalPages = Math.max(1, Math.ceil(filteredSessions.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageSessions = filteredSessions.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">My Sessions</h1>
        <p className="text-sm text-muted-foreground">View your scheduled and past coaching sessions.</p>
      </div>

      <SessionFilters
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => {
          setStatusFilter(v)
          setPage(1)
        }}
        meetingTypeFilter={meetingTypeFilter}
        onMeetingTypeFilterChange={(v) => {
          setMeetingTypeFilter(v)
          setPage(1)
        }}
        dateFilter={dateFilter}
        onDateFilterChange={(v) => {
          setDateFilter(v)
          setPage(1)
        }}
        errorMessage={sessionsQuery.isError ? getApiErrorMessage(sessionsQuery.error, "Unable to load your sessions.") : null}
      />

      {sessionsQuery.isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!sessionsQuery.isLoading && sessionsQuery.isError && (
        <ErrorState title="Unable to load sessions" message="Something went wrong while loading your sessions." onRetry={() => sessionsQuery.refetch()} />
      )}

      {!sessionsQuery.isLoading && !sessionsQuery.isError && filteredSessions.length === 0 && (
        <EmptyState icon={CalendarDays} message="No sessions found." />
      )}

      {!sessionsQuery.isLoading && !sessionsQuery.isError && filteredSessions.length > 0 && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Scheduled Start</th>
                  <th className="px-3 py-2 font-medium">Meeting Type</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Attendance</th>
                  <th className="px-3 py-2 font-medium">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {pageSessions.map((session) => (
                  <tr key={session.id} className="hover:bg-muted/30">
                    <td className="px-3 py-2.5 whitespace-nowrap font-medium">
                      <Link to={`/client/my-sessions/${session.id}`} className="hover:underline">
                        {formatDateTime(session.scheduled_start)}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                      {SESSION_MEETING_TYPE_LABELS[session.meeting_type]}
                    </td>
                    <td className="px-3 py-2.5">
                      <Badge variant={SESSION_STATUS_BADGE_VARIANT[session.status]}>
                        {SESSION_STATUS_LABELS[session.status]}
                      </Badge>
                    </td>
                    <td className="px-3 py-2.5">
                      <Badge variant={SESSION_ATTENDANCE_STATUS_BADGE_VARIANT[session.attendance_status ?? "NOT_RECORDED"]}>
                        {SESSION_ATTENDANCE_STATUS_LABELS[session.attendance_status ?? "NOT_RECORDED"]}
                      </Badge>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <Button variant="ghost" size="icon-sm" aria-label="View session" render={<Link to={`/client/my-sessions/${session.id}`} />} nativeButton={false}>
                        <Eye className="size-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>
                  <ChevronLeft className="size-4" />
                  Previous
                </Button>
                <Button variant="outline" size="sm" disabled={currentPage >= totalPages} onClick={() => setPage(currentPage + 1)}>
                  Next
                  <ChevronRight className="size-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
