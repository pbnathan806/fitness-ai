import type { SessionStatus } from "@/types/session"
import type { badgeVariants } from "@/components/ui/badge"
import type { VariantProps } from "class-variance-authority"

export const SESSION_STATUS_LABELS: Record<SessionStatus, string> = {
  SCHEDULED: "Scheduled",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
  RESCHEDULED: "Rescheduled",
}

export const SESSION_STATUS_BADGE_VARIANT: Record<
  SessionStatus,
  NonNullable<VariantProps<typeof badgeVariants>["variant"]>
> = {
  SCHEDULED: "default",
  COMPLETED: "success",
  CANCELLED: "destructive",
  RESCHEDULED: "warning",
}
