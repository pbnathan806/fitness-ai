import { useQuery } from "@tanstack/react-query"
import { CalendarCheck, CalendarClock, Percent } from "lucide-react"
import { dashboardService } from "@/services/dashboardService"
import { getApiErrorMessage } from "@/lib/errors"
import { ErrorState } from "@/components/common/ErrorState"
import { StatCard, StatCardSkeleton } from "@/app/pages/dashboard/components/StatCard"

/** Check-ins V2: replaces the old check_ins_this_week metric with
 * completed/expected/adherence, computed from sessions rather than calendar
 * days (see backend DashboardService.get_client_dashboard). */
export function ClientDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["dashboard", "client", "stats"],
    queryFn: dashboardService.getClientStats,
  })

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
        <h1 className="text-xl font-semibold">My Dashboard</h1>
        <p className="text-sm text-muted-foreground">Your check-in progress across all coaching sessions.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {statsQuery.isLoading || !stats ? (
          Array.from({ length: 3 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Completed Check-ins" value={stats.completed_check_ins} icon={CalendarCheck} tone="success" />
            <StatCard label="Expected Check-ins" value={stats.expected_check_ins} icon={CalendarClock} />
            <StatCard
              label="Adherence"
              value={stats.adherence_percentage}
              icon={Percent}
              tone={stats.adherence_percentage >= 70 ? "success" : "warning"}
              suffix="%"
            />
          </>
        )}
      </div>
    </div>
  )
}
