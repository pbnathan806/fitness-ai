import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { AlertTriangle, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { subscriptionService } from "@/services/subscriptionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate, formatDateTime } from "@/lib/format"
import type { Subscription } from "@/types/subscription"

const MAX_ITEMS = 10

function todayDateString(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

interface StaleSubscriptionsWidgetProps {
  clientNameById: Map<string, string>
}

/** Subscriptions still marked ACTIVE whose end_date has already passed.
 * status never auto-transitions to EXPIRED (no scheduled job exists), so
 * these accumulate silently unless a SUPER_ADMIN reviews and expires them
 * here. Expiring one also cancels its future SCHEDULED sessions (shown as a
 * preview before the admin confirms), so no session is left dangling under
 * a subscription that no longer covers it. */
export function StaleSubscriptionsWidget({ clientNameById }: StaleSubscriptionsWidgetProps) {
  const queryClient = useQueryClient()
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [checkingImpactId, setCheckingImpactId] = useState<string | null>(null)

  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", "all"],
    queryFn: subscriptionService.listAllSubscriptions,
  })

  const staleSubscriptions = useMemo(() => {
    const today = todayDateString()
    return (subscriptionsQuery.data ?? [])
      .filter((s) => s.status === "ACTIVE" && s.end_date < today)
      .sort((a, b) => a.end_date.localeCompare(b.end_date))
  }, [subscriptionsQuery.data])

  const visible = staleSubscriptions.slice(0, MAX_ITEMS)
  const hiddenCount = staleSubscriptions.length - visible.length

  const expireMutation = useMutation({
    mutationFn: (subscriptionId: string) => subscriptionService.expireSubscription(subscriptionId),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
      queryClient.invalidateQueries({ queryKey: ["sessions"] })
      // Cancelling sessions can change what the dashboard's own
      // upcoming-sessions/stats widgets should show (different query keys
      // from ["sessions"] - see dashboardService.listSessionsForUpcomingWidget).
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success(
        result.sessions_cancelled > 0
          ? `Subscription expired. ${result.sessions_cancelled} session(s) cancelled.`
          : "Subscription expired.",
      )
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to expire subscription."))
    },
    onSettled: () => setPendingId(null),
  })

  async function handleExpireClick(subscription: Subscription) {
    const clientName = clientNameById.get(subscription.client_id) ?? `Client #${subscription.client_id.slice(0, 8)}`

    setCheckingImpactId(subscription.id)
    let impact: Awaited<ReturnType<typeof subscriptionService.getExpiryImpact>>
    try {
      impact = await subscriptionService.getExpiryImpact(subscription.id)
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to check subscription expiry impact."))
      setCheckingImpactId(null)
      return
    }
    setCheckingImpactId(null)

    let message = `Expire ${clientName}'s "${subscription.plan_name}" subscription (ended ${formatDate(subscription.end_date)})?`
    if (impact.length > 0) {
      const preview = impact.slice(0, 5).map((s) => `- ${formatDateTime(s.scheduled_start)}`)
      if (impact.length > 5) preview.push(`...and ${impact.length - 5} more`)
      message += `\n\nThis will also CANCEL ${impact.length} upcoming session(s):\n${preview.join("\n")}\n\nThis cannot be undone.`
    }

    if (window.confirm(message)) {
      setPendingId(subscription.id)
      expireMutation.mutate(subscription.id)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="size-4 text-muted-foreground" aria-hidden="true" />
          Subscriptions Needing Expiry
        </CardTitle>
        <CardDescription>Still marked Active but past their end date.</CardDescription>
      </CardHeader>
      <CardContent>
        {subscriptionsQuery.isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!subscriptionsQuery.isLoading && subscriptionsQuery.isError && (
          <ErrorState
            message={getApiErrorMessage(subscriptionsQuery.error, "Unable to load subscriptions.")}
            onRetry={() => subscriptionsQuery.refetch()}
          />
        )}

        {!subscriptionsQuery.isLoading && !subscriptionsQuery.isError && staleSubscriptions.length === 0 && (
          <p className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            No stale subscriptions. Everything is up to date.
          </p>
        )}

        {visible.length > 0 && (
          <div className="space-y-3">
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Client</th>
                    <th className="px-3 py-2 font-medium">Plan</th>
                    <th className="px-3 py-2 font-medium">End Date</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {visible.map((subscription) => (
                    <tr key={subscription.id} className="hover:bg-muted/30">
                      <td className="max-w-[160px] truncate px-3 py-2.5 font-medium">
                        {clientNameById.get(subscription.client_id) ?? `Client #${subscription.client_id.slice(0, 8)}`}
                      </td>
                      <td className="max-w-[160px] truncate px-3 py-2.5 text-muted-foreground">
                        {subscription.plan_name}
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-destructive">
                        {formatDate(subscription.end_date)}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={checkingImpactId === subscription.id || pendingId === subscription.id}
                          onClick={() => handleExpireClick(subscription)}
                        >
                          {checkingImpactId === subscription.id
                            ? "Checking..."
                            : pendingId === subscription.id
                              ? "Expiring..."
                              : "Expire"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {hiddenCount > 0 && (
              <p className="text-xs text-muted-foreground">
                {hiddenCount} more not shown - visit the Subscriptions list to see all.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
