import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import type { SessionMeetingType, SessionStatus } from "@/types/session"

const STATUS_OPTIONS: SessionStatus[] = ["SCHEDULED", "COMPLETED", "CANCELLED", "RESCHEDULED"]
const MEETING_TYPE_OPTIONS: SessionMeetingType[] = ["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]

interface SessionFiltersProps {
  statusFilter: SessionStatus | "ALL"
  onStatusFilterChange: (value: SessionStatus | "ALL") => void
  meetingTypeFilter: SessionMeetingType | "ALL"
  onMeetingTypeFilterChange: (value: SessionMeetingType | "ALL") => void
  dateFilter: string
  onDateFilterChange: (value: string) => void
  errorMessage?: string | null
}

/** Client-side-only filter bar (Task 22.6) - `GET /sessions` has no
 * status/meeting-type/date query params, so every Sessions list page fetches
 * the full set (sessionService.listAllSessions/getMySessions) and filters
 * here in the browser, matching the precedent set by SubscriptionsListPage. */
export function SessionFilters({
  statusFilter,
  onStatusFilterChange,
  meetingTypeFilter,
  onMeetingTypeFilterChange,
  dateFilter,
  onDateFilterChange,
  errorMessage,
}: SessionFiltersProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Filters</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="session-status-filter">Status</Label>
            <Select
              id="session-status-filter"
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value as SessionStatus | "ALL")}
            >
              <option value="ALL">All statuses</option>
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {SESSION_STATUS_LABELS[status]}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="session-meeting-type-filter">Meeting Type</Label>
            <Select
              id="session-meeting-type-filter"
              value={meetingTypeFilter}
              onChange={(e) => onMeetingTypeFilterChange(e.target.value as SessionMeetingType | "ALL")}
            >
              <option value="ALL">All meeting types</option>
              {MEETING_TYPE_OPTIONS.map((type) => (
                <option key={type} value={type}>
                  {SESSION_MEETING_TYPE_LABELS[type]}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="session-date-filter">Date</Label>
            <Input
              id="session-date-filter"
              type="date"
              value={dateFilter}
              onChange={(e) => onDateFilterChange(e.target.value)}
            />
          </div>
        </div>

        {errorMessage && <p className="mt-3 text-xs text-destructive">{errorMessage}</p>}
      </CardContent>
    </Card>
  )
}
