import { Link, useParams, useSearchParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft, History } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { MeasurementCard } from "@/app/pages/measurements/components/MeasurementCard"
import { clientService } from "@/services/clientService"
import { measurementService } from "@/services/measurementService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"

/** Trainer-facing client measurements view: latest measurement (with inline
 * Add/Edit) plus full history. Reached from the Pending Measurements page's
 * row links, which pass ?action=add or ?action=edit to auto-open the right
 * form on arrival. */
export function TrainerClientMeasurementsPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const action = searchParams.get("action")
  const initialAction = action === "add" || action === "edit" ? action : null

  const clientQuery = useQuery({
    queryKey: ["clients", id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  })

  const historyQuery = useQuery({
    queryKey: ["measurements", "client", id],
    queryFn: () => measurementService.getClientMeasurements(id!),
    enabled: !!id,
  })

  if (clientQuery.isLoading) {
    return <LoadingSpinner label="Loading client..." className="py-16" />
  }

  if (clientQuery.isError || !clientQuery.data) {
    return (
      <ErrorState
        title="Unable to load client"
        message={getApiErrorMessage(clientQuery.error, "This client could not be found.")}
        onRetry={() => clientQuery.refetch()}
      />
    )
  }

  const client = clientQuery.data
  const history = historyQuery.data ?? []

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/trainer/pending-measurements" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to Pending Measurements
      </Button>

      <div>
        <h1 className="text-xl font-semibold">
          {client.first_name} {client.last_name}
        </h1>
        <p className="text-sm text-muted-foreground">{client.email}</p>
      </div>

      {id && <MeasurementCard clientId={id} initialAction={initialAction} />}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="size-4 text-muted-foreground" aria-hidden="true" />
            Measurement History
          </CardTitle>
          <CardDescription>Every measurement recorded for this client.</CardDescription>
        </CardHeader>
        <CardContent>
          {historyQuery.isLoading && <Skeleton className="h-24 w-full" />}

          {!historyQuery.isLoading && historyQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(historyQuery.error)}
              onRetry={() => historyQuery.refetch()}
            />
          )}

          {!historyQuery.isLoading && !historyQuery.isError && history.length === 0 && (
            <EmptyState icon={History} message="No measurements recorded yet." />
          )}

          {history.length > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Weight</th>
                    <th className="px-3 py-2 font-medium">Body Fat</th>
                    <th className="px-3 py-2 font-medium">Waist</th>
                    <th className="px-3 py-2 font-medium">Chest</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {history.map((measurement) => (
                    <tr key={measurement.id}>
                      <td className="px-3 py-2.5 whitespace-nowrap">{formatDate(measurement.recorded_at)}</td>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
