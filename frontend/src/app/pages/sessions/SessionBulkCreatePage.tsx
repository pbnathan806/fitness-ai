import { useEffect, useMemo } from "react"
import { Link } from "react-router-dom"
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
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { ErrorState } from "@/components/common/ErrorState"
import { clientService } from "@/services/clientService"
import { trainerService } from "@/services/trainerService"
import { assignmentService } from "@/services/assignmentService"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import type { SessionMeetingType, Weekday } from "@/types/session"

const LOOKUP_PAGE_SIZE = 100

const MEETING_TYPE_OPTIONS: SessionMeetingType[] = ["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]
const DAY_OPTIONS: { value: Weekday; label: string }[] = [
  { value: "MONDAY", label: "Monday" },
  { value: "TUESDAY", label: "Tuesday" },
  { value: "WEDNESDAY", label: "Wednesday" },
  { value: "THURSDAY", label: "Thursday" },
  { value: "FRIDAY", label: "Friday" },
  { value: "SATURDAY", label: "Saturday" },
  { value: "SUNDAY", label: "Sunday" },
]

const schema = z
  .object({
    client_id: z.string().min(1, "Client is required"),
    trainer_id: z.string().min(1, "Trainer is required"),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
    days: z.array(z.enum(["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"])).min(1, "Select at least one day"),
    start_time: z.string().min(1, "Start time is required"),
    duration_minutes: z.coerce.number().int().min(1, "Duration must be at least 1 minute"),
    meeting_type: z.enum(["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]),
  })
  .refine((values) => values.start_date <= values.end_date, {
    message: "Start date must be on or before end date",
    path: ["end_date"],
  })

type SessionBulkCreateFormValues = z.infer<typeof schema>

/** Bulk Session Creation page (Task 22.6), SUPER_ADMIN only per the route
 * table. `POST /sessions/bulk` skips (rather than fails) any individual slot
 * it can't schedule - e.g. an overlap or a session-limit conflict - so a
 * partial result with `skipped_reasons` is a normal outcome, not an error,
 * and is surfaced inline rather than treated as a mutation failure. */
export function SessionBulkCreatePage() {
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
  const assignmentsQuery = useQuery({
    queryKey: ["assignments", "lookup"],
    queryFn: assignmentService.listAssignmentsForLookup,
  })

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SessionBulkCreateFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SessionBulkCreateFormValues>,
    defaultValues: {
      client_id: "",
      trainer_id: "",
      start_date: "",
      end_date: "",
      days: [],
      start_time: "09:00",
      duration_minutes: 60,
      meeting_type: "GOOGLE_MEET",
    },
  })

  const selectedClientId = watch("client_id")

  /** Only trainers assigned to the selected client - the backend rejects
   * any other trainer with TrainerNotAssignedError anyway, so filtering
   * here just surfaces that constraint up front instead of after submit. */
  const assignableTrainers = useMemo(() => {
    if (!selectedClientId) return []
    const assignedTrainerIds = new Set(
      (assignmentsQuery.data ?? [])
        .filter((a) => a.client_id === selectedClientId)
        .map((a) => a.trainer_id),
    )
    return (trainersQuery.data?.items ?? []).filter((t) => assignedTrainerIds.has(t.id))
  }, [selectedClientId, assignmentsQuery.data, trainersQuery.data])

  // Changing the client can invalidate a previously selected trainer, so
  // clear it rather than leave a stale, now-unassigned trainer selected.
  useEffect(() => {
    setValue("trainer_id", "")
  }, [selectedClientId, setValue])

  const bulkCreateMutation = useMutation({
    mutationFn: (values: SessionBulkCreateFormValues) =>
      sessionService.bulkCreateSessions({
        client_id: values.client_id,
        trainer_id: values.trainer_id,
        start_date: values.start_date,
        end_date: values.end_date,
        days: values.days,
        start_time: `${values.start_time}:00`,
        duration_minutes: values.duration_minutes,
        meeting_type: values.meeting_type,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] })
      toast.success(`${result.sessions_created} session(s) created${result.sessions_skipped ? `, ${result.sessions_skipped} skipped` : ""}.`)
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
          <CardTitle>Bulk Session Creation</CardTitle>
          <CardDescription>Schedule recurring sessions across a date range.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => bulkCreateMutation.mutate(values))} noValidate className="space-y-4">
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
                  disabled={!selectedClientId || trainersQuery.isLoading || assignmentsQuery.isLoading}
                  defaultValue=""
                  {...register("trainer_id")}
                >
                  <option value="" disabled>
                    {selectedClientId ? "Select a trainer" : "Select a client first"}
                  </option>
                  {assignableTrainers.map((trainer) => (
                    <option key={trainer.id} value={trainer.id}>
                      {trainer.first_name} {trainer.last_name} ({trainer.email})
                    </option>
                  ))}
                </Select>
                {errors.trainer_id && <p className="text-sm text-destructive">{errors.trainer_id.message}</p>}
                {selectedClientId && !assignmentsQuery.isLoading && assignableTrainers.length === 0 && (
                  <p className="text-xs text-destructive">
                    This client has no assigned trainers.{" "}
                    <Link to={`/super-admin/clients/${selectedClientId}/trainers`} className="underline">
                      Assign one first
                    </Link>
                    .
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input id="start_date" type="date" aria-invalid={!!errors.start_date} {...register("start_date")} />
                {errors.start_date && <p className="text-sm text-destructive">{errors.start_date.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input id="end_date" type="date" aria-invalid={!!errors.end_date} {...register("end_date")} />
                {errors.end_date && <p className="text-sm text-destructive">{errors.end_date.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Days of Week</Label>
              <div className="flex flex-wrap gap-3">
                {DAY_OPTIONS.map((day) => (
                  <label key={day.value} className="flex items-center gap-1.5 text-sm">
                    <input
                      type="checkbox"
                      value={day.value}
                      className="size-4 rounded border-input accent-primary"
                      {...register("days")}
                    />
                    {day.label}
                  </label>
                ))}
              </div>
              {errors.days && <p className="text-sm text-destructive">{errors.days.message}</p>}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_time">Start Time</Label>
                <Input id="start_time" type="time" aria-invalid={!!errors.start_time} {...register("start_time")} />
                {errors.start_time && <p className="text-sm text-destructive">{errors.start_time.message}</p>}
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

            <div className="space-y-2 sm:max-w-xs">
              <Label htmlFor="meeting_type">Meeting Type</Label>
              <Select id="meeting_type" aria-invalid={!!errors.meeting_type} {...register("meeting_type")}>
                {MEETING_TYPE_OPTIONS.map((type) => (
                  <option key={type} value={type}>
                    {SESSION_MEETING_TYPE_LABELS[type]}
                  </option>
                ))}
              </Select>
            </div>

            {bulkCreateMutation.isError && (
              <ErrorState title="Couldn't create sessions" message={getApiErrorMessage(bulkCreateMutation.error)} />
            )}

            <Button type="submit" disabled={bulkCreateMutation.isPending} className="w-full sm:w-auto">
              {bulkCreateMutation.isPending ? "Creating..." : "Create Sessions"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {bulkCreateMutation.isSuccess && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">
              <span className="font-medium text-emerald-600 dark:text-emerald-400">{bulkCreateMutation.data.sessions_created}</span> created,{" "}
              <span className="font-medium text-amber-600 dark:text-amber-400">{bulkCreateMutation.data.sessions_skipped}</span> skipped.
            </p>
            {bulkCreateMutation.data.skipped_reasons.length > 0 && (
              <Alert>
                <AlertTitle>Skipped slots</AlertTitle>
                <AlertDescription>
                  <ul className="list-inside list-disc space-y-1">
                    {bulkCreateMutation.data.skipped_reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
