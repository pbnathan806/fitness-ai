import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Plus, Search } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { SubscriptionPlanTable } from "@/app/pages/subscriptionPlans/components/SubscriptionPlanTable"
import { subscriptionPlanService } from "@/services/subscriptionPlanService"
import { getApiErrorMessage } from "@/lib/errors"

const ACTIVE_FILTER_OPTIONS = ["ALL", "ACTIVE", "INACTIVE"] as const

export function SubscriptionPlansListPage() {
  const [search, setSearch] = useState("")
  const [activeFilter, setActiveFilter] = useState<(typeof ACTIVE_FILTER_OPTIONS)[number]>("ALL")

  const plansQuery = useQuery({
    queryKey: ["subscription-plans", "all"],
    queryFn: subscriptionPlanService.listPlans,
  })

  const filteredPlans = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (plansQuery.data ?? [])
      .filter((plan) => !term || plan.name.toLowerCase().includes(term))
      .filter((plan) => {
        if (activeFilter === "ALL") return true
        return activeFilter === "ACTIVE" ? plan.is_active : !plan.is_active
      })
  }, [plansQuery.data, search, activeFilter])

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Subscription Plans</h1>
          <p className="text-sm text-muted-foreground">Manage the catalog of plans clients can subscribe to.</p>
        </div>
        <Button render={<Link to="/super-admin/subscription-plans/new" />} nativeButton={false}>
          <Plus className="size-4" />
          New Plan
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Search &amp; Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5 lg:col-span-2">
              <Label htmlFor="plan-search">Search</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="plan-search"
                  placeholder="Search by name"
                  className="pl-7"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="plan-active-filter">Status</Label>
              <Select
                id="plan-active-filter"
                value={activeFilter}
                onChange={(e) => setActiveFilter(e.target.value as (typeof ACTIVE_FILTER_OPTIONS)[number])}
              >
                <option value="ALL">All statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </Select>
            </div>
          </div>

          {activeFilter === "INACTIVE" && (
            <p className="text-xs text-muted-foreground">
              The subscription plans API only returns active plans, so inactive plans cannot be listed here.
            </p>
          )}

          {plansQuery.isError && (
            <p className="text-xs text-destructive">
              {getApiErrorMessage(plansQuery.error, "Unable to load subscription plans.")}
            </p>
          )}
        </CardContent>
      </Card>

      <SubscriptionPlanTable
        plans={filteredPlans}
        isLoading={plansQuery.isLoading}
        isError={plansQuery.isError}
        onRetry={() => plansQuery.refetch()}
      />
    </div>
  )
}
