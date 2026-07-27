import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Plus, Search } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { ClientTable, type ClientRow } from "@/app/pages/clients/components/ClientTable"
import { clientService } from "@/services/clientService"
import { assignmentService } from "@/services/assignmentService"
import { subscriptionService } from "@/services/subscriptionService"
import { SUBSCRIPTION_STATUS_LABELS, type SubscriptionStatusValue } from "@/lib/subscriptionStatus"

const PAGE_SIZE = 10

const SUBSCRIPTION_FILTER_OPTIONS: (SubscriptionStatusValue | "ALL")[] = [
  "ALL",
  "ACTIVE",
  "EXPIRED",
  "PAUSED",
  "CANCELLED",
  "NONE",
]

function latestSubscriptionStatus(
  subscriptions: { client_id: string; status: SubscriptionStatusValue; start_date: string }[],
  clientId: string,
): SubscriptionStatusValue {
  const forClient = subscriptions.filter((s) => s.client_id === clientId)
  if (forClient.length === 0) return "NONE"
  return forClient.reduce((latest, current) => (current.start_date > latest.start_date ? current : latest)).status
}

export function ClientsListPage() {
  const [search, setSearch] = useState("")
  const [subscriptionFilter, setSubscriptionFilter] = useState<SubscriptionStatusValue | "ALL">("ALL")
  const [page, setPage] = useState(1)

  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })
  const assignmentsQuery = useQuery({
    queryKey: ["assignments", "lookup"],
    queryFn: assignmentService.listAssignmentsForLookup,
  })
  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", "lookup"],
    queryFn: subscriptionService.listSubscriptionsForLookup,
  })

  const trainerCountByClientId = useMemo(() => {
    const counts = new Map<string, number>()
    for (const assignment of assignmentsQuery.data ?? []) {
      counts.set(assignment.client_id, (counts.get(assignment.client_id) ?? 0) + 1)
    }
    return counts
  }, [assignmentsQuery.data])

  const filteredRows = useMemo<ClientRow[]>(() => {
    const term = search.trim().toLowerCase()
    const subscriptions = subscriptionsQuery.data ?? []

    return (clientsQuery.data ?? [])
      .filter((client) => {
        if (!term) return true
        return (
          client.first_name.toLowerCase().includes(term) ||
          client.last_name.toLowerCase().includes(term) ||
          client.email.toLowerCase().includes(term)
        )
      })
      .map((client) => ({
        client,
        trainerCount: trainerCountByClientId.get(client.id) ?? 0,
        subscriptionStatus: latestSubscriptionStatus(subscriptions, client.id),
      }))
      .filter((row) => subscriptionFilter === "ALL" || row.subscriptionStatus === subscriptionFilter)
  }, [clientsQuery.data, search, subscriptionFilter, subscriptionsQuery.data, trainerCountByClientId])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = filteredRows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const isLoading = clientsQuery.isLoading || assignmentsQuery.isLoading || subscriptionsQuery.isLoading
  const isError = clientsQuery.isError

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Clients</h1>
          <p className="text-sm text-muted-foreground">Manage client profiles, subscriptions, and trainer assignments.</p>
        </div>
        <Button render={<Link to="/super-admin/clients/new" />} nativeButton={false}>
          <Plus className="size-4" />
          New Client
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Search &amp; Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5 lg:col-span-2">
              <Label htmlFor="client-search">Search</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="client-search"
                  placeholder="Search by first name, last name, or email"
                  className="pl-7"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="subscription-filter">Subscription Status</Label>
              <Select
                id="subscription-filter"
                value={subscriptionFilter}
                onChange={(e) => {
                  setSubscriptionFilter(e.target.value as SubscriptionStatusValue | "ALL")
                  setPage(1)
                }}
              >
                {SUBSCRIPTION_FILTER_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status === "ALL" ? "All statuses" : SUBSCRIPTION_STATUS_LABELS[status]}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trainer-filter">Assigned Trainer</Label>
              <Select id="trainer-filter" disabled defaultValue="">
                <option value="">All trainers</option>
              </Select>
              <p className="text-xs text-muted-foreground">
                Trainer directory API is not yet available. This filter will be enabled in Task 22.4.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <ClientTable
        rows={pageRows}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => clientsQuery.refetch()}
        page={currentPage}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  )
}
