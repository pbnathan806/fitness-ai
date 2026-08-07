import { useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { SessionDetailsCard } from "@/app/pages/sessions/components/SessionDetailsCard"
import { SessionEditForm } from "@/app/pages/sessions/components/SessionEditForm"
import { SessionAttendanceForm } from "@/app/pages/sessions/components/SessionAttendanceForm"
import { SessionNotesForm } from "@/app/pages/sessions/components/SessionNotesForm"
import { SessionCheckInCard } from "@/app/pages/sessions/components/SessionCheckInCard"
import { assignmentService } from "@/services/assignmentService"
import { trainerService } from "@/services/trainerService"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SessionAttendanceStatus, SessionNotesUpdateInput, SessionUpdateInput } from "@/types/session"

/** Trainer's own session details (Task 22.6). Unlike the SUPER_ADMIN screens,
 * TRAINER has no separate `/trainer/sessions/:id/edit` route in the Task
 * 22.6 route table, so the scheduled_start/meeting_type/meeting_link/status
 * edit form is rendered inline here instead of on its own page. */
export function TrainerSessionDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const sessionQuery = useQuery({
    queryKey: ["sessions", id],
    queryFn: () => sessionService.getSession(id!),
    enabled: !!id,
  })

  // Resolved via the trainer's own assigned-clients roster (name only, no
  // PII) rather than GET /clients/{id} - trainers must not see a client's
  // email or phone number anywhere in the trainer-facing UI.
  const clientsQuery = useQuery({
    queryKey: ["assignments", "my-clients"],
    queryFn: assignmentService.getMyClients,
  })

  const trainerQuery = useQuery({
    queryKey: ["trainers", sessionQuery.data?.trainer_id],
    queryFn: () => trainerService.getTrainer(sessionQuery.data!.trainer_id),
    enabled: !!sessionQuery.data?.trainer_id,
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["sessions", "all"] })
  }

  const updateMutation = useMutation({
    mutationFn: (values: SessionUpdateInput) => sessionService.updateSession(id!, values),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sessions", id], updated)
      invalidate()
      toast.success("Session updated successfully.")
    },
  })

  const attendanceMutation = useMutation({
    mutationFn: (attendanceStatus: SessionAttendanceStatus) =>
      sessionService.updateSessionAttendance(id!, { attendance_status: attendanceStatus }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sessions", id], updated)
      invalidate()
      toast.success("Attendance updated.")
    },
  })

  const notesMutation = useMutation({
    mutationFn: (values: SessionNotesUpdateInput) => sessionService.updateSessionNotes(id!, values),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sessions", id], updated)
      invalidate()
      toast.success("Session notes updated.")
    },
  })

  if (sessionQuery.isLoading) {
    return <LoadingSpinner label="Loading session..." className="py-16" />
  }

  if (sessionQuery.isError || !sessionQuery.data) {
    return (
      <ErrorState
        title="Unable to load session"
        message={getApiErrorMessage(sessionQuery.error, "This session could not be found.")}
        onRetry={() => sessionQuery.refetch()}
      />
    )
  }

  const session = sessionQuery.data
  const assignedClient = clientsQuery.data?.find((c) => c.client_id === session.client_id)
  const clientName = assignedClient
    ? `${assignedClient.first_name} ${assignedClient.last_name}`
    : `Client #${session.client_id.slice(0, 8)}`
  const trainerName = trainerQuery.data
    ? `${trainerQuery.data.first_name ?? ""} ${trainerQuery.data.last_name ?? ""}`.trim() || trainerQuery.data.email
    : `Trainer #${session.trainer_id.slice(0, 8)}`

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/trainer/sessions" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to sessions
      </Button>

      <div>
        <h1 className="text-xl font-semibold">{clientsQuery.isLoading ? "Loading..." : clientName}</h1>
        <p className="text-sm text-muted-foreground">Session details</p>
      </div>

      <SessionDetailsCard session={session} clientName={clientName} trainerName={trainerName} />

      <SessionCheckInCard session={session} allowSubmit />

      <Card>
        <CardHeader>
          <CardTitle>Edit Session</CardTitle>
          <CardDescription>Update the scheduled start, meeting type, meeting link, or status.</CardDescription>
        </CardHeader>
        <CardContent>
          <SessionEditForm
            session={session}
            onSubmit={(values) => updateMutation.mutate(values)}
            isSubmitting={updateMutation.isPending}
            submitErrorMessage={updateMutation.isError ? getApiErrorMessage(updateMutation.error) : null}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Attendance</CardTitle>
          <CardDescription>Record who attended this session.</CardDescription>
        </CardHeader>
        <CardContent>
          <SessionAttendanceForm
            session={session}
            onSubmit={(attendanceStatus) => attendanceMutation.mutate(attendanceStatus)}
            isSubmitting={attendanceMutation.isPending}
            submitErrorMessage={attendanceMutation.isError ? getApiErrorMessage(attendanceMutation.error) : null}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session Notes</CardTitle>
          <CardDescription>Trainer notes, feedback, homework, and next session focus.</CardDescription>
        </CardHeader>
        <CardContent>
          <SessionNotesForm
            session={session}
            onSubmit={(values) => notesMutation.mutate(values)}
            isSubmitting={notesMutation.isPending}
            submitErrorMessage={notesMutation.isError ? getApiErrorMessage(notesMutation.error) : null}
          />
        </CardContent>
      </Card>
    </div>
  )
}
