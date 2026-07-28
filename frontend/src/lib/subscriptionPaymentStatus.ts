import type { SubscriptionPaymentStatus } from "@/types/subscription"
import type { badgeVariants } from "@/components/ui/badge"
import type { VariantProps } from "class-variance-authority"

export const SUBSCRIPTION_PAYMENT_STATUS_LABELS: Record<SubscriptionPaymentStatus, string> = {
  PAID: "Paid",
  PENDING: "Pending",
  FAILED: "Failed",
  REFUNDED: "Refunded",
}

export const SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT: Record<
  SubscriptionPaymentStatus,
  NonNullable<VariantProps<typeof badgeVariants>["variant"]>
> = {
  PAID: "success",
  PENDING: "warning",
  FAILED: "destructive",
  REFUNDED: "secondary",
}
