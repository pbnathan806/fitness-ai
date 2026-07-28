import type { PaginatedResponse } from "@/types/dashboard"

export type SessionStatus = "SCHEDULED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED"

export type SessionMeetingType = "GOOGLE_MEET" | "ZOOM" | "WHATSAPP" | "PHONE" | "IN_PERSON"

export type SessionAttendanceStatus =
  | "PRESENT"
  | "BOTH_PRESENT"
  | "CLIENT_NO_SHOW"
  | "TRAINER_NO_SHOW"
  | "LATE"
  | "RESCHEDULED"

export type Weekday = "MONDAY" | "TUESDAY" | "WEDNESDAY" | "THURSDAY" | "FRIDAY" | "SATURDAY" | "SUNDAY"

export interface Session {
  id: string
  client_id: string
  trainer_id: string
  scheduled_start: string
  scheduled_end: string
  duration_minutes: number
  status: SessionStatus
  meeting_type: SessionMeetingType
  meeting_link: string | null
  trainer_notes: string | null
  trainer_feedback: string | null
  homework: string | null
  next_session_focus: string | null
  attendance_status: SessionAttendanceStatus | null
  created_at: string
  updated_at: string
}

export type PaginatedSessions = PaginatedResponse<Session>

export interface SessionCreateInput {
  client_id: string
  trainer_id?: string | null
  scheduled_start: string
  duration_minutes: number
  meeting_type: SessionMeetingType
  meeting_link?: string | null
  trainer_notes?: string | null
}

export interface SessionBulkCreateInput {
  client_id: string
  trainer_id?: string | null
  start_date: string
  end_date: string
  days: Weekday[]
  start_time: string
  duration_minutes: number
  meeting_type: SessionMeetingType
}

export interface SessionBulkCreateResult {
  sessions_created: number
  sessions_skipped: number
  skipped_reasons: string[]
}

/** Only scheduled_start, meeting_type, meeting_link, and status are editable
 * via `PATCH /sessions/{id}` per Task 22.6 - attendance and notes go through
 * their own dedicated endpoints/inputs below. */
export interface SessionUpdateInput {
  scheduled_start?: string
  meeting_type?: SessionMeetingType
  meeting_link?: string | null
  status?: SessionStatus
}

export interface SessionNotesUpdateInput {
  trainer_notes?: string | null
  trainer_feedback?: string | null
  homework?: string | null
  next_session_focus?: string | null
}

export interface SessionAttendanceUpdateInput {
  attendance_status: SessionAttendanceStatus
}

/** Narrower view used by the Client "My Sessions" screens - deliberately
 * omits trainer_notes, trainer_feedback, and next_session_focus, which
 * clients must never see (Task 22.6 requirement 8). */
export type ClientSessionView = Omit<Session, "trainer_notes" | "trainer_feedback" | "next_session_focus">
