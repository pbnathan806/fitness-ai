import { useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { ChevronLeft, Pencil, Plus, UserCog, CreditCard, CalendarClock, Ruler, ClipboardCheck } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ClientDetailsCard } from "@/app/pages/clients/components/ClientDetailsCard"
import { TrainerAssignmentCard } from "@/app/pages/clients/components/TrainerAssignmentCard"
import { SubscriptionEligibilityBadge } from "@/components/common/SubscriptionEligibilityBadge"
import { MeasurementForm } from "@/app/pages/measurements/components/MeasurementForm"
import { clientService } from "@/services/clientService"
import { assignmentService } from "@/services/assignmentService"
import { subscriptionService } from "@/services/subscriptionService"
import { measurementService } from "@/services/measurementService"
import { checkInService } from "@/services/checkInService"
import { dashboardService } from "@/services/dashboardService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate, formatDateTime } from "@/lib/format"
import { SUBSCRIPTION_STATUS_BADGE_VARIANT, SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import type { MeasurementCreateInput, MeasurementUpdateInput } from "@/types/measurement"

export function ClientDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [isAddingMeasurement, setIsAddingMeasurement] = useState(false)

  const clientQuery = useQuery({
    queryKey: ["clients", id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  })

  const assignmentsQuery = useQuery({
    queryKey: ["assignments", "lookup"],
    queryFn: assignmentService.listAssignmentsForLookup,
  })

  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", "lookup"],
    queryFn: subscriptionService.listSubscriptionsForLookup,
  })

  const sessionsQuery = useQuery({
    queryKey: ["sessions", "lookup"],
    queryFn: dashboardService.listSessionsForUpcomingWidget,
  })

  const measurementQuery = useQuery({
    queryKey: ["measurements", "latest", id],
    queryFn: () => measurementService.getLatestMeasurement(id!),
    enabled: !!id,
  })

  const checkInsQuery = useQuery({
    queryKey: ["check-ins", "client", id],
    queryFn: () => checkInService.getClientCheckIns(id!),
    enabled: !!id,
  })

  const createMeasurementMutation = useMutation({
    mutationFn: (values: MeasurementUpdateInput) =>
      measurementService.create({ client_id: id!, recorded_at: null, ...values } as MeasurementCreateInput),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["measurements", "latest", id] })
      setIsAddingMeasurement(false)
      toast.success("Measurement recorded.")
    },
  })

  const clientAssignments = useMemo(
    () => (assignmentsQuery.data ?? []).filter((a) => a.client_id === id),
    [assignmentsQuery.data, id],
  )

  const latestSubscription = useMemo(() => {
    const forClient = (subscriptionsQuery.data ?? []).filter((s) => s.client_id === id)
    if (forClient.length === 0) return null
    return forClient.reduce((latest, current) => (current.start_date > latest.start_date ? current : latest))
  }, [subscriptionsQuery.data, id])

  const upcomingSessions = useMemo(() => {
    const now = new Date()
    return (sessionsQuery.data ?? [])
      .filter((s) => s.client_id === id && s.status !== "CANCELLED" && new Date(s.scheduled_start) >= now)
      .sort((a, b) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime())
      .slice(0, 5)
  }, [sessionsQuery.data, id])

  const recentCheckIns = useMemo(() => {
    return [...(checkInsQuery.data ?? [])]
      .sort((a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime())
      .slice(0, 5)
  }, [checkInsQuery.data])

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
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Button variant="ghost" size="sm" render={<Link to="/super-admin/clients" />} nativeButton={false}>
          <ChevronLeft className="size-4" />
          Back to clients
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" render={<Link to={`/super-admin/clients/${id}/trainers`} />} nativeButton={false}>
            <UserCog className="size-4" />
            Manage Trainers
          </Button>
          <Button render={<Link to={`/super-admin/clients/${id}/edit`} />} nativeButton={false}>
            <Pencil className="size-4" />
            Edit Client
          </Button>
        </div>
      </div>

      <div>
        <h1 className="text-xl font-semibold">
          {client.first_name} {client.last_name}
        </h1>
        <p className="text-sm text-muted-foreground">{client.email}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ClientDetailsCard client={client} />

        <TrainerAssignmentCard
          assignments={clientAssignments}
          isLoading={assignmentsQuery.isLoading}
          isError={assignmentsQuery.isError}
          onRetry={() => assignmentsQuery.refetch()}
          variant="summary"
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="size-4 text-muted-foreground" aria-hidden="true" />
              Subscription Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">Eligibility</p>
              <div className="mt-1">{id && <SubscriptionEligibilityBadge clientId={id} />}</div>
            </div>

            {subscriptionsQuery.isLoading && <Skeleton className="h-16 w-full" />}
            {!subscriptionsQuery.isLoading && subscriptionsQuery.isError && (
              <ErrorState message="Unable to load subscriptions." onRetry={() => subscriptionsQuery.refetch()} />
            )}
            {!subscriptionsQuery.isLoading && !subscriptionsQuery.isError && !latestSubscription && (
              <EmptyState icon={CreditCard} message="No subscriptions available." />
            )}
            {latestSubscription && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{latestSubscription.plan_name}</p>
                  <Badge variant={SUBSCRIPTION_STATUS_BADGE_VARIANT[latestSubscription.status]}>
                    {SUBSCRIPTION_STATUS_LABELS[latestSubscription.status]}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Start Date</p>
                    <p className="text-sm font-medium">{formatDate(latestSubscription.start_date)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">End Date</p>
                    <p className="text-sm font-medium">{formatDate(latestSubscription.end_date)}</p>
                  </div>
                </div>
              </div>
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
              <EmptyState icon={CalendarClock} message="No sessions found." />
            )}
            {upcomingSessions.length > 0 && (
              <ul className="divide-y">
                {upcomingSessions.map((session) => (
                  <li key={session.id} className="py-2 first:pt-0 last:pb-0">
                    <p className="text-sm font-medium">{formatDateTime(session.scheduled_start)}</p>
                    <p className="text-xs text-muted-foreground">{session.meeting_type} &middot; {session.status}</p>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="flex items-center gap-2">
                <Ruler className="size-4 text-muted-foreground" aria-hidden="true" />
                Latest Measurements
              </CardTitle>
              {!isAddingMeasurement && (
                <Button size="sm" onClick={() => setIsAddingMeasurement(true)}>
                  <Plus className="size-4" />
                  Add Measurement
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {!isAddingMeasurement && (
              <>
                {measurementQuery.isLoading && <Skeleton className="h-16 w-full" />}
                {!measurementQuery.isLoading && measurementQuery.isError && (
                  <ErrorState message="Unable to load measurements." onRetry={() => measurementQuery.refetch()} />
                )}
                {!measurementQuery.isLoading && !measurementQuery.isError && !measurementQuery.data && (
                  <EmptyState icon={Ruler} message="No measurements available." />
                )}
                {measurementQuery.data && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Date</p>
                      <p className="text-sm font-medium">
                        {measurementQuery.data.recorded_at ? formatDate(measurementQuery.data.recorded_at) : "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Weight</p>
                      <p className="text-sm font-medium">
                        {measurementQuery.data.weight_kg != null ? `${measurementQuery.data.weight_kg} kg` : "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Waist</p>
                      <p className="text-sm font-medium">
                        {measurementQuery.data.waist_cm != null ? `${measurementQuery.data.waist_cm} cm` : "N/A"}
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}

            {isAddingMeasurement && (
              <>
                <MeasurementForm
                  onSubmit={(values) => createMeasurementMutation.mutate(values)}
                  isSubmitting={createMeasurementMutation.isPending}
                  submitErrorMessage={
                    createMeasurementMutation.isError ? getApiErrorMessage(createMeasurementMutation.error) : null
                  }
                  submitLabel="Save Measurement"
                />
                <Button variant="ghost" size="sm" onClick={() => setIsAddingMeasurement(false)}>
                  Cancel
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardCheck className="size-4 text-muted-foreground" aria-hidden="true" />
              Recent Check-ins
            </CardTitle>
            <CardDescription>Last 5 check-ins</CardDescription>
          </CardHeader>
          <CardContent>
            {checkInsQuery.isLoading && <Skeleton className="h-16 w-full" />}
            {!checkInsQuery.isLoading && checkInsQuery.isError && (
              <ErrorState message="Unable to load check-ins." onRetry={() => checkInsQuery.refetch()} />
            )}
            {!checkInsQuery.isLoading && !checkInsQuery.isError && recentCheckIns.length === 0 && (
              <EmptyState icon={ClipboardCheck} message="No check-ins found." />
            )}
            {recentCheckIns.length > 0 && (
              <ul className="divide-y">
                {recentCheckIns.map((checkIn) => (
                  <li key={checkIn.id} className="py-2 first:pt-0 last:pb-0">
                    <p className="text-sm font-medium">{formatDateTime(checkIn.submitted_at)}</p>
                    <p className="text-xs text-muted-foreground">
                      {checkIn.mood != null ? `Mood ${checkIn.mood}/5` : "Mood N/A"} &middot;{" "}
                      {checkIn.energy_level != null ? `Energy ${checkIn.energy_level}/5` : "Energy N/A"}
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
