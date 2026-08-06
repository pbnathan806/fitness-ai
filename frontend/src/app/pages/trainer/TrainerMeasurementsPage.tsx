import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Ruler, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { measurementService } from "@/services/measurementService"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"

type Tab = "pending" | "all"

/** Trainer's own measurements: a Pending queue (assigned clients overdue for
 * their next measurement, mirrors the existing pending-measurements screen)
 * and an All log (every recorded measurement for assigned clients, newest
 * first, mirroring SuperAdminMeasurementsPage's "All Measurements" table
 * shape). Adding/editing a measurement already works via the per-client page
 * (`/trainer/clients/:id`) - both tabs link into that same existing
 * capability. */
export function TrainerMeasurementsPage() {
  const [tab, setTab] = useState<Tab>("pending")

  const pendingQuery = useQuery({
    queryKey: ["measurements", "pending"],
    queryFn: measurementService.listPending,
    enabled: tab === "pending",
  })

  const allQuery = useQuery({
    queryKey: ["measurements", "all"],
    queryFn: measurementService.listAllMeasurements,
    enabled: tab === "all",
  })

  const clientsQuery = useQuery({
    queryKey: ["clients", "all"],
    queryFn: clientService.listAllClients,
    enabled: tab === "all",
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const sortedMeasurements = useMemo(() => {
    return [...(allQuery.data ?? [])].sort(
      (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime(),
    )
  }, [allQuery.data])

  const allIsLoading = allQuery.isLoading || clientsQuery.isLoading
  const allIsError = allQuery.isError

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Measurements</h1>
        <p className="text-sm text-muted-foreground">Body measurements for your assigned clients.</p>
      </div>

      <div className="flex gap-2">
        <Button variant={tab === "pending" ? "default" : "outline"} size="sm" onClick={() => setTab("pending")}>
          Pending
        </Button>
        <Button variant={tab === "all" ? "default" : "outline"} size="sm" onClick={() => setTab("all")}>
          All
        </Button>
      </div>

      {tab === "pending" && (
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
      )}

      {tab === "all" && (
        <Card>
          <CardHeader>
            <CardTitle>All Measurements</CardTitle>
            <CardDescription>Every measurement recorded for your assigned clients, newest first.</CardDescription>
          </CardHeader>
          <CardContent>
            {allIsLoading && (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            )}

            {!allIsLoading && allIsError && (
              <ErrorState
                message={getApiErrorMessage(allQuery.error, "Unable to load measurements.")}
                onRetry={() => allQuery.refetch()}
              />
            )}

            {!allIsLoading && !allIsError && sortedMeasurements.length === 0 && (
              <EmptyState icon={Ruler} message="No measurements found." />
            )}

            {!allIsLoading && !allIsError && sortedMeasurements.length > 0 && (
              <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Client</th>
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">Weight</th>
                      <th className="px-3 py-2 font-medium">Body Fat</th>
                      <th className="px-3 py-2 font-medium">Waist</th>
                      <th className="px-3 py-2 font-medium">Chest</th>
                      <th className="px-3 py-2 font-medium">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {sortedMeasurements.map((measurement) => (
                      <tr key={measurement.id} className="hover:bg-muted/30">
                        <td className="max-w-[180px] truncate px-3 py-2.5 font-medium">
                          {clientNameById.get(measurement.client_id) ?? `Client #${measurement.client_id.slice(0, 8)}`}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                          {formatDate(measurement.recorded_at)}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {measurement.weight_kg != null ? `${measurement.weight_kg} kg` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {measurement.body_fat_percentage != null ? `${measurement.body_fat_percentage} %` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {measurement.waist_cm != null ? `${measurement.waist_cm} cm` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {measurement.chest_cm != null ? `${measurement.chest_cm} cm` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-right whitespace-nowrap">
                          <Button
                            variant="ghost"
                            size="sm"
                            render={<Link to={`/trainer/clients/${measurement.client_id}`} />}
                            nativeButton={false}
                          >
                            <Eye className="size-4" />
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
