import { useQuery } from "@tanstack/react-query"
import { CreditCard } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { subscriptionService } from "@/services/subscriptionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { SUBSCRIPTION_STATUS_BADGE_VARIANT, SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import {
  SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT,
  SUBSCRIPTION_PAYMENT_STATUS_LABELS,
} from "@/lib/subscriptionPaymentStatus"

export function ClientSubscriptionsPage() {
  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", "my-subscriptions"],
    queryFn: subscriptionService.getMySubscriptions,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">My Subscriptions</h1>
        <p className="text-sm text-muted-foreground">View your subscription plans and their status.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="size-4 text-muted-foreground" aria-hidden="true" />
            Subscriptions
          </CardTitle>
        </CardHeader>
        <CardContent>
          {subscriptionsQuery.isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          )}

          {!subscriptionsQuery.isLoading && subscriptionsQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(subscriptionsQuery.error, "Unable to load your subscriptions.")}
              onRetry={() => subscriptionsQuery.refetch()}
            />
          )}

          {!subscriptionsQuery.isLoading && !subscriptionsQuery.isError && (subscriptionsQuery.data?.length ?? 0) === 0 && (
            <EmptyState icon={CreditCard} message="You do not currently have any subscriptions." />
          )}

          {(subscriptionsQuery.data?.length ?? 0) > 0 && (
            <ul className="divide-y">
              {subscriptionsQuery.data!.map((subscription) => (
                <li key={subscription.id} className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">{subscription.plan_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(subscription.start_date)} &ndash; {formatDate(subscription.end_date)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={SUBSCRIPTION_STATUS_BADGE_VARIANT[subscription.status]}>
                      {SUBSCRIPTION_STATUS_LABELS[subscription.status]}
                    </Badge>
                    <Badge variant={SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT[subscription.payment_status]}>
                      {SUBSCRIPTION_PAYMENT_STATUS_LABELS[subscription.payment_status]}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
