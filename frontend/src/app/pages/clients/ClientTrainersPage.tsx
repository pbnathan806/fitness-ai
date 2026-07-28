import { useMemo } from "react"
import { Link, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/common/ErrorState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { TrainerAssignmentCard } from "@/app/pages/clients/components/TrainerAssignmentCard"
import { clientService } from "@/services/clientService"
import { assignmentService } from "@/services/assignmentService"
import { getApiErrorMessage } from "@/lib/errors"

export function ClientTrainersPage() {
  const { id } = useParams<{ id: string }>()

  const clientQuery = useQuery({
    queryKey: ["clients", id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  })

  const assignmentsQuery = useQuery({
    queryKey: ["assignments", "lookup"],
    queryFn: assignmentService.listAssignmentsForLookup,
  })

  const clientAssignments = useMemo(
    () => (assignmentsQuery.data ?? []).filter((a) => a.client_id === id),
    [assignmentsQuery.data, id],
  )

  if (clientQuery.isLoading) {
    return <LoadingSpinner label="Loading client details..." className="py-16" />
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

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to={`/super-admin/clients/${id}`} />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to client
      </Button>

      <div>
        <h1 className="text-xl font-semibold">
          Manage Trainers &mdash; {client.first_name} {client.last_name}
        </h1>
        <p className="text-sm text-muted-foreground">View, assign, and remove this client's trainers.</p>
      </div>

      <TrainerAssignmentCard
        clientId={id}
        assignments={clientAssignments}
        isLoading={assignmentsQuery.isLoading}
        isError={assignmentsQuery.isError}
        onRetry={() => assignmentsQuery.refetch()}
        variant="full"
      />
    </div>
  )
}
