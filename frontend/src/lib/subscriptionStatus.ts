import type { SubscriptionStatus } from "@/types/subscription"
import type { badgeVariants } from "@/components/ui/badge"
import type { VariantProps } from "class-variance-authority"

export type SubscriptionStatusValue = SubscriptionStatus | "NONE"

export const SUBSCRIPTION_STATUS_LABELS: Record<SubscriptionStatusValue, string> = {
  ACTIVE: "Active",
  EXPIRED: "Expired",
  PAUSED: "Paused",
  CANCELLED: "Cancelled",
  NONE: "No Subscription",
}

export const SUBSCRIPTION_STATUS_BADGE_VARIANT: Record<
  SubscriptionStatusValue,
  NonNullable<VariantProps<typeof badgeVariants>["variant"]>
> = {
  ACTIVE: "success",
  EXPIRED: "destructive",
  PAUSED: "warning",
  CANCELLED: "secondary",
  NONE: "secondary",
}
