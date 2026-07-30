import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Ruler } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { measurementService } from "@/services/measurementService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"

/** Clients assigned to the current trainer whose latest measurement is
 * overdue against the configured measurement frequency (see backend
 * MeasurementService.list_pending_measurements). Clients never measured at
 * all don't appear here - only clients with a measurement history that's
 * gone stale. */
export function TrainerPendingMeasurementsPage() {
  const pendingQuery = useQuery({
    queryKey: ["measurements", "pending"],
    queryFn: measurementService.listPending,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Pending Measurements</h1>
        <p className="text-sm text-muted-foreground">
          Assigned clients who are overdue for their next measurement.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>Pending Measurements</CardTitle>
            {!pendingQuery.isLoading && !pendingQuery.isError && (
              <Badge variant={pendingQuery.data && pendingQuery.data.length > 0 ? "warning" : "secondary"}>
                {pendingQuery.data?.length ?? 0} pending
              </Badge>
            )}
          </div>
          <CardDescription>Add a new measurement, edit the most recent one, or view full history.</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingQuery.isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          )}

          {!pendingQuery.isLoading && pendingQuery.isError && (
            <ErrorState message={getApiErrorMessage(pendingQuery.error)} onRetry={() => pendingQuery.refetch()} />
          )}

          {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data?.length === 0 && (
            <EmptyState icon={Ruler} message="No pending measurements. Everything is up to date." />
          )}

          {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data && pendingQuery.data.length > 0 && (
            <ul className="divide-y">
              {pendingQuery.data.map((item) => (
                <li key={item.client_id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between gap-3">
                    <Link to={`/trainer/clients/${item.client_id}`} className="min-w-0 flex-1 hover:underline">
                      <p className="text-sm font-medium">{item.client_name}</p>
                      <p className="text-xs text-muted-foreground">
                        Last measured {formatDate(item.last_measurement_date)}
                      </p>
                    </Link>
                    <Badge variant="warning" className="shrink-0">
                      {item.days_overdue} day{item.days_overdue === 1 ? "" : "s"} overdue
                    </Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      render={<Link to={`/trainer/clients/${item.client_id}?action=add`} />}
                      nativeButton={false}
                    >
                      Add Measurement
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      render={<Link to={`/trainer/clients/${item.client_id}?action=edit`} />}
                      nativeButton={false}
                    >
                      Edit Measurement
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      render={<Link to={`/trainer/clients/${item.client_id}`} />}
                      nativeButton={false}
                    >
                      View History
                    </Button>
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
