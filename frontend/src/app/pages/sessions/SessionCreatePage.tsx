import { useNavigate, Link } from "react-router-dom"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ErrorState } from "@/components/common/ErrorState"
import { fromDateTimeLocalValue } from "@/app/pages/sessions/components/dateTimeLocal"
import { clientService } from "@/services/clientService"
import { trainerService } from "@/services/trainerService"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import type { SessionMeetingType } from "@/types/session"

const LOOKUP_PAGE_SIZE = 100

const MEETING_TYPE_OPTIONS: SessionMeetingType[] = ["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]

const schema = z.object({
  client_id: z.string().min(1, "Client is required"),
  trainer_id: z.string().min(1, "Trainer is required"),
  scheduled_start: z.string().min(1, "Scheduled start is required"),
  duration_minutes: z.coerce.number().int().min(1, "Duration must be at least 1 minute"),
  meeting_type: z.enum(["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]),
  meeting_link: z.string().optional().or(z.literal("")),
  trainer_notes: z.string().optional().or(z.literal("")),
})

type SessionCreateFormValues = z.infer<typeof schema>

/** Create Session page (Task 22.6), SUPER_ADMIN only per the route table -
 * `trainer_id` is required here since a Super Admin is not themselves a
 * trainer (the backend infers it automatically when a TRAINER creates their
 * own session, but that flow has no route in this task). */
export function SessionCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })
  const trainersQuery = useQuery({
    queryKey: ["trainers", "lookup"],
    queryFn: () =>
      trainerService.listTrainers({
        page: 1,
        page_size: LOOKUP_PAGE_SIZE,
        is_active: true,
        sort_by: "first_name",
        sort_dir: "asc",
      }),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SessionCreateFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SessionCreateFormValues>,
    defaultValues: {
      client_id: "",
      trainer_id: "",
      scheduled_start: "",
      duration_minutes: 60,
      meeting_type: "GOOGLE_MEET",
      meeting_link: "",
      trainer_notes: "",
    },
  })

  const createMutation = useMutation({
    mutationFn: (values: SessionCreateFormValues) =>
      sessionService.createSession({
        client_id: values.client_id,
        trainer_id: values.trainer_id,
        scheduled_start: fromDateTimeLocalValue(values.scheduled_start),
        duration_minutes: values.duration_minutes,
        meeting_type: values.meeting_type,
        meeting_link: values.meeting_link || null,
        trainer_notes: values.trainer_notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] })
      toast.success("Session created successfully.")
      navigate("/super-admin/sessions")
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/sessions" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to sessions
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>New Session</CardTitle>
          <CardDescription>Schedule a coaching session for a client.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => createMutation.mutate(values))} noValidate className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="client_id">Client</Label>
                <Select
                  id="client_id"
                  aria-invalid={!!errors.client_id}
                  disabled={clientsQuery.isLoading}
                  defaultValue=""
                  {...register("client_id")}
                >
                  <option value="" disabled>
                    Select a client
                  </option>
                  {(clientsQuery.data ?? []).map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.first_name} {client.last_name} ({client.email})
                    </option>
                  ))}
                </Select>
                {errors.client_id && <p className="text-sm text-destructive">{errors.client_id.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="trainer_id">Trainer</Label>
                <Select
                  id="trainer_id"
                  aria-invalid={!!errors.trainer_id}
                  disabled={trainersQuery.isLoading}
                  defaultValue=""
                  {...register("trainer_id")}
                >
                  <option value="" disabled>
                    Select a trainer
                  </option>
                  {(trainersQuery.data?.items ?? []).map((trainer) => (
                    <option key={trainer.id} value={trainer.id}>
                      {trainer.first_name} {trainer.last_name} ({trainer.email})
                    </option>
                  ))}
                </Select>
                {errors.trainer_id && <p className="text-sm text-destructive">{errors.trainer_id.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="scheduled_start">Scheduled Start</Label>
                <Input
                  id="scheduled_start"
                  type="datetime-local"
                  aria-invalid={!!errors.scheduled_start}
                  {...register("scheduled_start")}
                />
                {errors.scheduled_start && <p className="text-sm text-destructive">{errors.scheduled_start.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="duration_minutes">Duration (minutes)</Label>
                <Input
                  id="duration_minutes"
                  type="number"
                  min={1}
                  aria-invalid={!!errors.duration_minutes}
                  {...register("duration_minutes")}
                />
                {errors.duration_minutes && <p className="text-sm text-destructive">{errors.duration_minutes.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="meeting_type">Meeting Type</Label>
                <Select id="meeting_type" aria-invalid={!!errors.meeting_type} {...register("meeting_type")}>
                  {MEETING_TYPE_OPTIONS.map((type) => (
                    <option key={type} value={type}>
                      {SESSION_MEETING_TYPE_LABELS[type]}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="meeting_link">Meeting Link</Label>
                <Input id="meeting_link" aria-invalid={!!errors.meeting_link} {...register("meeting_link")} />
                {errors.meeting_link && <p className="text-sm text-destructive">{errors.meeting_link.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="trainer_notes">Trainer Notes</Label>
              <Textarea id="trainer_notes" aria-invalid={!!errors.trainer_notes} {...register("trainer_notes")} />
              {errors.trainer_notes && <p className="text-sm text-destructive">{errors.trainer_notes.message}</p>}
            </div>

            {createMutation.isError && (
              <ErrorState title="Couldn't create session" message={getApiErrorMessage(createMutation.error)} />
            )}

            <Button type="submit" disabled={createMutation.isPending} className="w-full sm:w-auto">
              {createMutation.isPending ? "Saving..." : "Create Session"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
