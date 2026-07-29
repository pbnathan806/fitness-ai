import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Users, UserCheck, UserX, UserCog, CalendarCheck, CalendarRange, ClipboardX, Ruler } from "lucide-react"
import { dashboardService } from "@/services/dashboardService"
import { getApiErrorMessage } from "@/lib/errors"
import { ErrorState } from "@/components/common/ErrorState"
import { StatCard, StatCardSkeleton } from "@/app/pages/dashboard/components/StatCard"
import { UpcomingSessionsWidget } from "@/app/pages/dashboard/components/UpcomingSessionsWidget"
import { RecentActivityWidget } from "@/app/pages/dashboard/components/RecentActivityWidget"
import { AlertsWidget } from "@/app/pages/dashboard/components/AlertsWidget"
import { QuickActionsWidget } from "@/app/pages/dashboard/components/QuickActionsWidget"
import { StaleSubscriptionsWidget } from "@/app/pages/dashboard/components/StaleSubscriptionsWidget"

export function SuperAdminDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "stats"],
    queryFn: dashboardService.getSuperAdminStats,
  })

  const sessionsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "upcoming-sessions"],
    queryFn: dashboardService.listSessionsForUpcomingWidget,
  })

  const checkInsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "recent-check-ins"],
    queryFn: dashboardService.listRecentCheckIns,
  })

  const measurementsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "recent-measurements"],
    queryFn: dashboardService.listRecentMeasurements,
  })

  const clientsQuery = useQuery({
    queryKey: ["dashboard", "super-admin", "clients-lookup"],
    queryFn: dashboardService.listClientsForNameLookup,
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const activityIsLoading = checkInsQuery.isLoading || measurementsQuery.isLoading
  const activityIsError = checkInsQuery.isError || measurementsQuery.isError

  if (statsQuery.isError) {
    return (
      <ErrorState
        title="Couldn't load the dashboard"
        message={getApiErrorMessage(statsQuery.error)}
        onRetry={() => statsQuery.refetch()}
      />
    )
  }

  const stats = statsQuery.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Super Admin Dashboard</h1>
        <p className="text-sm text-muted-foreground">Platform-wide overview of clients, trainers, and activity.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {statsQuery.isLoading || !stats ? (
          Array.from({ length: 8 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Total Clients" value={stats.total_clients} icon={Users} />
            <StatCard label="Active Clients" value={stats.active_clients} icon={UserCheck} tone="success" />
            <StatCard label="Expired Clients" value={stats.expired_clients} icon={UserX} tone="destructive" />
            <StatCard label="Total Trainers" value={stats.total_trainers} icon={UserCog} />
            <StatCard label="Today's Sessions" value={stats.sessions_today} icon={CalendarCheck} />
            <StatCard
              label="Upcoming Sessions (7d)"
              value={stats.upcoming_sessions_next_7_days}
              icon={CalendarRange}
            />
            <StatCard
              label="Measurements This Month"
              value={stats.measurements_recorded_this_month}
              icon={Ruler}
            />
            <StatCard
              label="Missing Check-ins Today"
              value={stats.clients_missing_check_ins_today}
              icon={ClipboardX}
              tone="warning"
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <UpcomingSessionsWidget
            sessions={sessionsQuery.data}
            clientNameById={clientNameById}
            isLoading={sessionsQuery.isLoading}
            isError={sessionsQuery.isError}
            onRetry={() => sessionsQuery.refetch()}
          />
          <RecentActivityWidget
            checkIns={checkInsQuery.data}
            measurements={measurementsQuery.data}
            clientNameById={clientNameById}
            isLoading={activityIsLoading}
            isError={activityIsError}
            onRetry={() => {
              checkInsQuery.refetch()
              measurementsQuery.refetch()
            }}
          />
          <StaleSubscriptionsWidget clientNameById={clientNameById} />
        </div>
        <div className="space-y-4">
          <AlertsWidget
            stats={statsQuery.data}
            isLoading={statsQuery.isLoading}
            isError={statsQuery.isError}
            onRetry={() => statsQuery.refetch()}
          />
          <QuickActionsWidget />
        </div>
      </div>
    </div>
  )
}
