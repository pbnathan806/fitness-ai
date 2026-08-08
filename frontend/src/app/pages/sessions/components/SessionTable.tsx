import { Link, useNavigate } from "react-router-dom"
import { Eye, ChevronLeft, ChevronRight, CalendarDays } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { useDisplayTimezone } from "@/lib/displayTimezone"
import { formatDateTime } from "@/lib/format"
import { SESSION_STATUS_BADGE_VARIANT, SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import {
  SESSION_ATTENDANCE_STATUS_BADGE_VARIANT,
  SESSION_ATTENDANCE_STATUS_LABELS,
} from "@/lib/sessionAttendanceStatus"
import type { Session } from "@/types/session"

export interface SessionRow {
  session: Session
  clientName: string
  trainerName: string
}

interface SessionTableProps {
  rows: SessionRow[]
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  /** Relative to the current role section, e.g. "/super-admin/sessions". */
  basePath: string
}

/** Reusable sessions list table (Task 22.6), shared by the SUPER_ADMIN and
 * TRAINER Sessions screens. Pagination is client-side - see
 * sessionService.listAllSessions - since `GET /sessions` has no
 * status/meeting-type/date query params. */
export function SessionTable({ rows, isLoading, isError, onRetry, page, totalPages, onPageChange, basePath }: SessionTableProps) {
  const navigate = useNavigate()
  const timezone = useDisplayTimezone()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return <ErrorState title="Unable to load sessions" message="Something went wrong while loading sessions." onRetry={onRetry} />
  }

  if (rows.length === 0) {
    return <EmptyState icon={CalendarDays} message="No sessions found." />
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Client</th>
              <th className="px-3 py-2 font-medium">Trainer</th>
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
            {rows.map(({ session, clientName, trainerName }) => (
              <tr key={session.id} className="hover:bg-muted/30">
                <td className="max-w-[160px] truncate px-3 py-2.5 font-medium">
                  <Link to={`${basePath}/${session.id}`} className="hover:underline">
                    {clientName}
                  </Link>
                </td>
                <td className="max-w-[160px] truncate px-3 py-2.5 text-muted-foreground">{trainerName}</td>
                <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{formatDateTime(session.scheduled_start, timezone)}</td>
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
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="View session"
                    onClick={() => navigate(`${basePath}/${session.id}`)}
                  >
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
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              <ChevronLeft className="size-4" />
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              Next
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
