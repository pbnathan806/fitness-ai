import { useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft, Pencil } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { SessionDetailsCard } from "@/app/pages/sessions/components/SessionDetailsCard"
import { SessionAttendanceForm } from "@/app/pages/sessions/components/SessionAttendanceForm"
import { SessionNotesForm } from "@/app/pages/sessions/components/SessionNotesForm"
import { SessionCheckInCard } from "@/app/pages/sessions/components/SessionCheckInCard"
import { clientService } from "@/services/clientService"
import { trainerService } from "@/services/trainerService"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SessionAttendanceStatus, SessionNotesUpdateInput } from "@/types/session"

export function SessionDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const sessionQuery = useQuery({
    queryKey: ["sessions", id],
    queryFn: () => sessionService.getSession(id!),
    enabled: !!id,
  })

  const clientQuery = useQuery({
    queryKey: ["clients", sessionQuery.data?.client_id],
    queryFn: () => clientService.getClient(sessionQuery.data!.client_id),
    enabled: !!sessionQuery.data?.client_id,
  })

  const trainerQuery = useQuery({
    queryKey: ["trainers", sessionQuery.data?.trainer_id],
    queryFn: () => trainerService.getTrainer(sessionQuery.data!.trainer_id),
    enabled: !!sessionQuery.data?.trainer_id,
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["sessions", "all"] })
  }

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
  const clientName = clientQuery.data ? `${clientQuery.data.first_name} ${clientQuery.data.last_name}` : `Client #${session.client_id.slice(0, 8)}`
  const trainerName = trainerQuery.data
    ? `${trainerQuery.data.first_name ?? ""} ${trainerQuery.data.last_name ?? ""}`.trim() || trainerQuery.data.email
    : `Trainer #${session.trainer_id.slice(0, 8)}`

  // The Trainer API never exposes a trainer's underlying user id (only their
  // profile id), so a submission can only be positively attributed to the
  // client; anything else is coaching staff acting on the client's behalf.
  function resolveSubmittedBy(submittedByUserId: string): string {
    if (clientQuery.data?.user_id === submittedByUserId) {
      return `${clientName} (Client)`
    }
    return "Trainer or Super Admin"
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" render={<Link to="/super-admin/sessions" />} nativeButton={false}>
          <ChevronLeft className="size-4" />
          Back to sessions
        </Button>
        <Button variant="outline" size="sm" render={<Link to={`/super-admin/sessions/${id}/edit`} />} nativeButton={false}>
          <Pencil className="size-4" />
          Edit Session
        </Button>
      </div>

      <div>
        <h1 className="text-xl font-semibold">{clientName}</h1>
        <p className="text-sm text-muted-foreground">{trainerQuery.isLoading ? "Loading trainer..." : trainerName}</p>
      </div>

      <SessionDetailsCard session={session} clientName={clientName} trainerName={trainerName} />

      <SessionCheckInCard session={session} allowSubmit resolveSubmittedBy={resolveSubmittedBy} />

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
