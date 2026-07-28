import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { SubscriptionTable, type SubscriptionRow } from "@/app/pages/subscriptions/components/SubscriptionTable"
import { subscriptionService } from "@/services/subscriptionService"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"
import { SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import { SUBSCRIPTION_PAYMENT_STATUS_LABELS } from "@/lib/subscriptionPaymentStatus"
import type { SubscriptionPaymentStatus, SubscriptionStatus } from "@/types/subscription"

const PAGE_SIZE = 10

const STATUS_FILTER_OPTIONS: (SubscriptionStatus | "ALL")[] = ["ALL", "ACTIVE", "EXPIRED", "PAUSED", "CANCELLED"]
const PAYMENT_STATUS_FILTER_OPTIONS: (SubscriptionPaymentStatus | "ALL")[] = [
  "ALL",
  "PAID",
  "PENDING",
  "FAILED",
  "REFUNDED",
]

export function SubscriptionsListPage() {
  const [statusFilter, setStatusFilter] = useState<SubscriptionStatus | "ALL">("ALL")
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<SubscriptionPaymentStatus | "ALL">("ALL")
  const [page, setPage] = useState(1)

  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", "all"],
    queryFn: subscriptionService.listAllSubscriptions,
  })
  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const filteredRows = useMemo<SubscriptionRow[]>(() => {
    return (subscriptionsQuery.data ?? [])
      .filter((s) => statusFilter === "ALL" || s.status === statusFilter)
      .filter((s) => paymentStatusFilter === "ALL" || s.payment_status === paymentStatusFilter)
      .map((subscription) => ({
        subscription,
        clientName: clientNameById.get(subscription.client_id) ?? `Client #${subscription.client_id.slice(0, 8)}`,
      }))
  }, [subscriptionsQuery.data, statusFilter, paymentStatusFilter, clientNameById])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = filteredRows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const isLoading = subscriptionsQuery.isLoading || clientsQuery.isLoading
  const isError = subscriptionsQuery.isError

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Subscriptions</h1>
          <p className="text-sm text-muted-foreground">Manage client subscriptions.</p>
        </div>
        <Button render={<Link to="/super-admin/subscriptions/new" />} nativeButton={false}>
          <Plus className="size-4" />
          New Subscription
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="subscription-status-filter">Status</Label>
              <Select
                id="subscription-status-filter"
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as SubscriptionStatus | "ALL")
                  setPage(1)
                }}
              >
                <option value="ALL">All statuses</option>
                {STATUS_FILTER_OPTIONS.filter((s) => s !== "ALL").map((status) => (
                  <option key={status} value={status}>
                    {SUBSCRIPTION_STATUS_LABELS[status]}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="subscription-payment-status-filter">Payment Status</Label>
              <Select
                id="subscription-payment-status-filter"
                value={paymentStatusFilter}
                onChange={(e) => {
                  setPaymentStatusFilter(e.target.value as SubscriptionPaymentStatus | "ALL")
                  setPage(1)
                }}
              >
                <option value="ALL">All payment statuses</option>
                {PAYMENT_STATUS_FILTER_OPTIONS.filter((s) => s !== "ALL").map((status) => (
                  <option key={status} value={status}>
                    {SUBSCRIPTION_PAYMENT_STATUS_LABELS[status]}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          {isError && (
            <p className="mt-3 text-xs text-destructive">
              {getApiErrorMessage(subscriptionsQuery.error, "Unable to load subscriptions.")}
            </p>
          )}
        </CardContent>
      </Card>

      <SubscriptionTable
        rows={pageRows}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => subscriptionsQuery.refetch()}
        page={currentPage}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  )
}
