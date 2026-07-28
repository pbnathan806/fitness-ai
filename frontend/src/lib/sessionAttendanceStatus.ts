import type { SessionAttendanceStatus } from "@/types/session"
import type { badgeVariants } from "@/components/ui/badge"
import type { VariantProps } from "class-variance-authority"

export type SessionAttendanceStatusValue = SessionAttendanceStatus | "NOT_RECORDED"

export const SESSION_ATTENDANCE_STATUS_LABELS: Record<SessionAttendanceStatusValue, string> = {
  PRESENT: "Present",
  BOTH_PRESENT: "Both Present",
  CLIENT_NO_SHOW: "Client No-Show",
  TRAINER_NO_SHOW: "Trainer No-Show",
  LATE: "Late",
  RESCHEDULED: "Rescheduled",
  NOT_RECORDED: "Not Recorded",
}

export const SESSION_ATTENDANCE_STATUS_BADGE_VARIANT: Record<
  SessionAttendanceStatusValue,
  NonNullable<VariantProps<typeof badgeVariants>["variant"]>
> = {
  PRESENT: "success",
  BOTH_PRESENT: "success",
  CLIENT_NO_SHOW: "destructive",
  TRAINER_NO_SHOW: "destructive",
  LATE: "warning",
  RESCHEDULED: "warning",
  NOT_RECORDED: "secondary",
}
