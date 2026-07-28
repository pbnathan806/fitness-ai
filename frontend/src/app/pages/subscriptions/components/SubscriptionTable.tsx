import { Link, useNavigate } from "react-router-dom"
import { Eye, ChevronLeft, ChevronRight, CreditCard, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDate } from "@/lib/format"
import { SUBSCRIPTION_STATUS_BADGE_VARIANT, SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import {
  SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT,
  SUBSCRIPTION_PAYMENT_STATUS_LABELS,
} from "@/lib/subscriptionPaymentStatus"
import type { Subscription } from "@/types/subscription"

export interface SubscriptionRow {
  subscription: Subscription
  clientName: string
}

interface SubscriptionTableProps {
  rows: SubscriptionRow[]
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

/** Reusable subscriptions list table (Task 22.5). Pagination is client-side
 * (see subscriptionService.listAllSubscriptions) - the backend's
 * `GET /subscriptions` has no status/payment-status query params, so the
 * full list is fetched once and filtered/paginated in the browser, matching
 * the precedent set by ClientTable/clientService.listAllClients. */
export function SubscriptionTable({ rows, isLoading, isError, onRetry, page, totalPages, onPageChange }: SubscriptionTableProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorState title="Unable to load subscriptions" message="Something went wrong while loading subscriptions." onRetry={onRetry} />
    )
  }

  if (rows.length === 0) {
    return <EmptyState icon={CreditCard} message="No subscriptions found." />
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Client</th>
              <th className="px-3 py-2 font-medium">Plan Name</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Payment Status</th>
              <th className="px-3 py-2 font-medium">Start Date</th>
              <th className="px-3 py-2 font-medium">End Date</th>
              <th className="px-3 py-2 font-medium">Auto Renew</th>
              <th className="px-3 py-2 font-medium">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map(({ subscription, clientName }) => (
              <tr key={subscription.id} className="hover:bg-muted/30">
                <td className="max-w-[200px] truncate px-3 py-2.5 font-medium">
                  <Link to={`/super-admin/subscriptions/${subscription.id}`} className="hover:underline">
                    {clientName}
                  </Link>
                </td>
                <td className="max-w-[200px] truncate px-3 py-2.5 text-muted-foreground">{subscription.plan_name}</td>
                <td className="px-3 py-2.5">
                  <Badge variant={SUBSCRIPTION_STATUS_BADGE_VARIANT[subscription.status]}>
                    {SUBSCRIPTION_STATUS_LABELS[subscription.status]}
                  </Badge>
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant={SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT[subscription.payment_status]}>
                    {SUBSCRIPTION_PAYMENT_STATUS_LABELS[subscription.payment_status]}
                  </Badge>
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{formatDate(subscription.start_date)}</td>
                <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{formatDate(subscription.end_date)}</td>
                <td className="px-3 py-2.5">
                  {subscription.auto_renew ? (
                    <Check className="size-4 text-emerald-600 dark:text-emerald-400" aria-label="Auto renew enabled" />
                  ) : (
                    <X className="size-4 text-muted-foreground" aria-label="Auto renew disabled" />
                  )}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="View subscription"
                    onClick={() => navigate(`/super-admin/subscriptions/${subscription.id}`)}
                  >
                    <Eye className="size-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              <ChevronLeft className="size-4" />
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              Next
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

