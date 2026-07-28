import { useMemo } from "react"
import { Link, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft, Pencil, Users, CalendarClock, Ban, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { TrainerDetailsCard } from "@/app/pages/trainers/components/TrainerDetailsCard"
import { TrainerSummaryCard } from "@/app/pages/trainers/components/TrainerSummaryCard"
import { TrainerPerformanceCard } from "@/app/pages/trainers/components/TrainerPerformanceCard"
import { assignmentService } from "@/services/assignmentService"
import { clientService } from "@/services/clientService"
import { dashboardService } from "@/services/dashboardService"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"

export function TrainerDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const trainerQuery = useQuery({
    queryKey: ["trainers", id],
    queryFn: () => trainerService.getTrainer(id!),
    enabled: !!id,
  })

  const summaryQuery = useQuery({
    queryKey: ["trainers", id, "summary"],
    queryFn: () => trainerService.getSummary(id!),
    enabled: !!id,
  })

  const performanceQuery = useQuery({
    queryKey: ["trainers", id, "performance"],
    queryFn: () => trainerService.getPerformance(id!),
    enabled: !!id,
  })

  const assignmentsQuery = useQuery({
    queryKey: ["assignments", "lookup"],
    queryFn: assignmentService.listAssignmentsForLookup,
  })

  const clientsQuery = useQuery({
    queryKey: ["clients", "all"],
    queryFn: clientService.listAllClients,
  })

  const sessionsQuery = useQuery({
    queryKey: ["sessions", "lookup"],
    queryFn: dashboardService.listSessionsForUpcomingWidget,
  })

  const statusMutation = useMutation({
    mutationFn: () => trainerService.updateTrainerStatus(id!, !trainerQuery.data?.is_active),
    onSuccess: (updated) => {
      queryClient.setQueryData(["trainers", id], updated)
      queryClient.invalidateQueries({ queryKey: ["trainers", "list"] })
      toast.success(updated.is_active ? "Trainer activated." : "Trainer deactivated.")
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to update trainer status."))
    },
  })

  function handleToggleStatus() {
    if (!trainerQuery.data) return
    const action = trainerQuery.data.is_active ? "deactivate" : "activate"
    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${trainerQuery.data.first_name} ${trainerQuery.data.last_name}?`,
    )
    if (confirmed) {
      statusMutation.mutate()
    }
  }

  const trainerAssignments = useMemo(
    () => (assignmentsQuery.data ?? []).filter((a) => a.trainer_id === id),
    [assignmentsQuery.data, id],
  )

  const assignedClients = useMemo(() => {
    const clientIds = new Set(trainerAssignments.map((a) => a.client_id))
    return (clientsQuery.data ?? []).filter((c) => clientIds.has(c.id))
  }, [clientsQuery.data, trainerAssignments])

  const upcomingSessions = useMemo(() => {
    const now = new Date()
    return (sessionsQuery.data ?? [])
      .filter((s) => s.trainer_id === id && s.status !== "CANCELLED" && new Date(s.scheduled_start) >= now)
      .sort((a, b) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime())
      .slice(0, 5)
  }, [sessionsQuery.data, id])

  if (!id) {
    return <ErrorState title="Unable to load trainer details" message="No trainer id was provided." />
  }

  if (trainerQuery.isLoading) {
    return <LoadingSpinner label="Loading trainer details..." className="py-16" />
  }

  if (trainerQuery.isError || !trainerQuery.data) {
    return (
      <ErrorState
        title="Unable to load trainer"
        message={getApiErrorMessage(trainerQuery.error, "This trainer could not be found.")}
        onRetry={() => trainerQuery.refetch()}
      />
    )
  }

  const trainer = trainerQuery.data

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Button variant="ghost" size="sm" render={<Link to="/super-admin/trainers" />} nativeButton={false}>
          <ChevronLeft className="size-4" />
          Back to trainers
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" disabled={statusMutation.isPending} onClick={handleToggleStatus}>
            {trainer.is_active ? (
              <>
                <Ban className="size-4" />
                Deactivate
              </>
            ) : (
              <>
                <CheckCircle2 className="size-4" />
                Activate
              </>
            )}
          </Button>
          <Button render={<Link to={`/super-admin/trainers/${id}/edit`} />} nativeButton={false}>
            <Pencil className="size-4" />
            Edit Trainer
          </Button>
        </div>
      </div>

      <div>
        <h1 className="text-xl font-semibold">
          {trainer.first_name} {trainer.last_name}
        </h1>
        <p className="text-sm text-muted-foreground">{trainer.email}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrainerDetailsCard trainer={trainer} />

        <TrainerSummaryCard
          summary={summaryQuery.data}
          isLoading={summaryQuery.isLoading}
          isError={summaryQuery.isError}
          onRetry={() => summaryQuery.refetch()}
        />

        <TrainerPerformanceCard
          performance={performanceQuery.data}
          isLoading={performanceQuery.isLoading}
          isError={performanceQuery.isError}
          onRetry={() => performanceQuery.refetch()}
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="size-4 text-muted-foreground" aria-hidden="true" />
              Assigned Clients
            </CardTitle>
            <CardDescription>{trainerAssignments.length} assigned</CardDescription>
          </CardHeader>
          <CardContent>
            {clientsQuery.isLoading && <Skeleton className="h-16 w-full" />}
            {!clientsQuery.isLoading && clientsQuery.isError && (
              <ErrorState message="Unable to load assigned clients." onRetry={() => clientsQuery.refetch()} />
            )}
            {!clientsQuery.isLoading && !clientsQuery.isError && assignedClients.length === 0 && (
              <EmptyState icon={Users} message="No assigned clients." />
            )}
            {assignedClients.length > 0 && (
              <ul className="divide-y">
                {assignedClients.slice(0, 5).map((client) => (
                  <li key={client.id} className="py-2 first:pt-0 last:pb-0">
                    <Link to={`/super-admin/clients/${client.id}`} className="text-sm font-medium hover:underline">
                      {client.first_name} {client.last_name}
                    </Link>
                    <p className="text-xs text-muted-foreground">{client.email}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarClock className="size-4 text-muted-foreground" aria-hidden="true" />
              Upcoming Sessions
            </CardTitle>
            <CardDescription>Next 5 sessions</CardDescription>
          </CardHeader>
          <CardContent>
            {sessionsQuery.isLoading && <Skeleton className="h-16 w-full" />}
            {!sessionsQuery.isLoading && sessionsQuery.isError && (
              <ErrorState message="Unable to load sessions." onRetry={() => sessionsQuery.refetch()} />
            )}
            {!sessionsQuery.isLoading && !sessionsQuery.isError && upcomingSessions.length === 0 && (
              <EmptyState icon={CalendarClock} message="No upcoming sessions." />
            )}
            {upcomingSessions.length > 0 && (
              <ul className="divide-y">
                {upcomingSessions.map((session) => (
                  <li key={session.id} className="py-2 first:pt-0 last:pb-0">
                    <p className="text-sm font-medium">{formatDateTime(session.scheduled_start)}</p>
                    <p className="text-xs text-muted-foreground">
                      {session.meeting_type} &middot; {session.status}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
