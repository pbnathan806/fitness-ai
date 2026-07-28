import { useQuery } from "@tanstack/react-query"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { subscriptionService } from "@/services/subscriptionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"

interface SubscriptionEligibilityBadgeProps {
  clientId: string
}

/** Reusable eligibility indicator backed by `GET /subscriptions/client/{id}/eligibility`
 * (Task 22.5). Meant for SUPER_ADMIN/TRAINER screens that need a quick read on
 * whether a client can be scheduled - Client Details today, and Session
 * Creation/Scheduling once that module exists (currently a placeholder screen). */
export function SubscriptionEligibilityBadge({ clientId }: SubscriptionEligibilityBadgeProps) {
  const eligibilityQuery = useQuery({
    queryKey: ["subscriptions", "eligibility", clientId],
    queryFn: () => subscriptionService.getClientEligibility(clientId),
    enabled: !!clientId,
  })

  if (eligibilityQuery.isLoading) {
    return <Skeleton className="h-5 w-28" />
  }

  // A 404 here means the client has no subscriptions at all (or, for a
  // trainer, a 403 means they aren't assigned) - either way the client can't
  // be scheduled, so this reads as "Not Eligible" rather than a hard error.
  if (eligibilityQuery.isError || !eligibilityQuery.data) {
    return (
      <Badge variant="secondary" title={getApiErrorMessage(eligibilityQuery.error, "No subscription found.")}>
        Not Eligible
      </Badge>
    )
  }

  const eligibility = eligibilityQuery.data

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={eligibility.can_schedule_sessions ? "success" : "destructive"}>
        {eligibility.can_schedule_sessions ? "Eligible" : "Not Eligible"}
      </Badge>
      <span className="text-xs text-muted-foreground">
        {eligibility.plan_name} &middot; {SUBSCRIPTION_STATUS_LABELS[eligibility.status]} &middot; Ends{" "}
        {formatDate(eligibility.end_date)}
      </span>
    </div>
  )
}
