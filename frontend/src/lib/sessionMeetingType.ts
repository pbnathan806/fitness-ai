import type { SessionMeetingType } from "@/types/session"

export const SESSION_MEETING_TYPE_LABELS: Record<SessionMeetingType, string> = {
  GOOGLE_MEET: "Google Meet",
  ZOOM: "Zoom",
  WHATSAPP: "WhatsApp",
  PHONE: "Phone",
  IN_PERSON: "In Person",
}
