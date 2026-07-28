import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ErrorState } from "@/components/common/ErrorState"
import { SESSION_ATTENDANCE_STATUS_LABELS } from "@/lib/sessionAttendanceStatus"
import type { Session, SessionAttendanceStatus } from "@/types/session"

const ATTENDANCE_OPTIONS: SessionAttendanceStatus[] = [
  "PRESENT",
  "BOTH_PRESENT",
  "CLIENT_NO_SHOW",
  "TRAINER_NO_SHOW",
  "LATE",
  "RESCHEDULED",
]

interface SessionAttendanceFormProps {
  session: Session
  onSubmit: (attendanceStatus: SessionAttendanceStatus) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
}

/** Attendance management (Task 22.6 requirement 6) via `PATCH
 * /sessions/{id}/attendance`. Once a session is COMPLETED the backend
 * rejects further attendance edits (AttendanceImmutableError, surfaced here
 * as a 409 through submitErrorMessage). */
export function SessionAttendanceForm({ session, onSubmit, isSubmitting, submitErrorMessage }: SessionAttendanceFormProps) {
  const [attendanceStatus, setAttendanceStatus] = useState<SessionAttendanceStatus>(
    session.attendance_status ?? "PRESENT",
  )

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit(attendanceStatus)
      }}
      className="space-y-4"
    >
      <div className="space-y-2 sm:max-w-xs">
        <Label htmlFor="attendance_status">Attendance</Label>
        <Select
          id="attendance_status"
          value={attendanceStatus}
          onChange={(e) => setAttendanceStatus(e.target.value as SessionAttendanceStatus)}
        >
          {ATTENDANCE_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {SESSION_ATTENDANCE_STATUS_LABELS[status]}
            </option>
          ))}
        </Select>
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't update attendance" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : "Save Attendance"}
      </Button>
    </form>
  )
}
