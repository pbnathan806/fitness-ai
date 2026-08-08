import { Link, useParams, useSearchParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft, History } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { PhysicalAssessmentCard } from "@/app/pages/physicalAssessments/components/PhysicalAssessmentCard"
import { assignmentService } from "@/services/assignmentService"
import { physicalAssessmentService } from "@/services/physicalAssessmentService"
import { getApiErrorMessage } from "@/lib/errors"
import { useDisplayTimezone } from "@/lib/displayTimezone"
import { formatDate } from "@/lib/format"

/** Trainer-facing client physical assessments view: latest physical
 * assessment (with inline Add/Edit) plus full history. Reached from the
 * Physical Assessments page's Pending tab row links, which pass
 * ?action=add or ?action=edit to auto-open the right form on arrival.
 * Client identity is resolved via the trainer's own assigned-clients
 * roster (name only, no PII) rather than GET /clients/{id} - trainers must
 * not see a client's email or phone number anywhere in the trainer-facing
 * UI. */
export function TrainerClientPhysicalAssessmentsPage() {
  const timezone = useDisplayTimezone()
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const action = searchParams.get("action")
  const initialAction = action === "add" || action === "edit" ? action : null

  const clientsQuery = useQuery({
    queryKey: ["assignments", "my-clients"],
    queryFn: assignmentService.getMyClients,
  })

  const historyQuery = useQuery({
    queryKey: ["physical-assessments", "client", id],
    queryFn: () => physicalAssessmentService.getClientPhysicalAssessments(id!),
    enabled: !!id,
  })

  if (clientsQuery.isLoading) {
    return <LoadingSpinner label="Loading client..." className="py-16" />
  }

  const client = clientsQuery.data?.find((c) => c.client_id === id)

  if (clientsQuery.isError || !client) {
    return (
      <ErrorState
        title="Unable to load client"
        message={
          clientsQuery.isError
            ? getApiErrorMessage(clientsQuery.error)
            : "This client is not assigned to you."
        }
        onRetry={() => clientsQuery.refetch()}
      />
    )
  }

  const history = historyQuery.data ?? []

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/trainer/physical-assessments" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to Physical Assessments
      </Button>

      <div>
        <h1 className="text-xl font-semibold">
          {client.first_name} {client.last_name}
        </h1>
      </div>

      {id && <PhysicalAssessmentCard clientId={id} initialAction={initialAction} />}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="size-4 text-muted-foreground" aria-hidden="true" />
            Physical Assessment History
          </CardTitle>
          <CardDescription>
            Every physical assessment recorded for this client.
            {timezone && ` Dates use your profile timezone (${timezone}).`}
          </CardDescription>
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
            <EmptyState icon={History} message="No physical assessments recorded yet." />
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
                  {history.map((physicalAssessment) => (
                    <tr key={physicalAssessment.id}>
                      <td className="px-3 py-2.5 whitespace-nowrap">{formatDate(physicalAssessment.recorded_at, timezone)}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">
                        {physicalAssessment.weight_kg != null ? `${physicalAssessment.weight_kg} kg` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-muted-foreground">
                        {physicalAssessment.body_fat_percentage != null ? `${physicalAssessment.body_fat_percentage} %` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-muted-foreground">
                        {physicalAssessment.waist_cm != null ? `${physicalAssessment.waist_cm} cm` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-muted-foreground">
                        {physicalAssessment.chest_cm != null ? `${physicalAssessment.chest_cm} cm` : "—"}
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
