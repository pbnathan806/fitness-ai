import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ErrorState } from "@/components/common/ErrorState"
import { toDateTimeLocalValue, fromDateTimeLocalValue } from "@/app/pages/sessions/components/dateTimeLocal"
import { SESSION_STATUS_LABELS } from "@/lib/sessionStatus"
import { SESSION_MEETING_TYPE_LABELS } from "@/lib/sessionMeetingType"
import type { Session, SessionMeetingType, SessionStatus, SessionUpdateInput } from "@/types/session"

const STATUS_OPTIONS: SessionStatus[] = ["SCHEDULED", "COMPLETED", "CANCELLED", "RESCHEDULED"]
const MEETING_TYPE_OPTIONS: SessionMeetingType[] = ["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]

const schema = z.object({
  scheduled_start: z.string().min(1, "Scheduled start is required"),
  meeting_type: z.enum(["GOOGLE_MEET", "ZOOM", "WHATSAPP", "PHONE", "IN_PERSON"]),
  meeting_link: z.string().optional().or(z.literal("")),
  status: z.enum(["SCHEDULED", "COMPLETED", "CANCELLED", "RESCHEDULED"]),
})

type SessionEditFormValues = z.infer<typeof schema>

interface SessionEditFormProps {
  session: Session
  onSubmit: (values: SessionUpdateInput) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
}

/** Edit form for the only fields Task 22.6 allows mutating this way -
 * scheduled_start, meeting_type, meeting_link, and status. Rendered
 * standalone on the SUPER_ADMIN `/super-admin/sessions/:id/edit` route, and
 * inline on the TRAINER session details page (which has no separate edit
 * route per the Task 22.6 route table). */
export function SessionEditForm({ session, onSubmit, isSubmitting, submitErrorMessage }: SessionEditFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SessionEditFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SessionEditFormValues>,
    defaultValues: {
      scheduled_start: toDateTimeLocalValue(session.scheduled_start),
      meeting_type: session.meeting_type,
      meeting_link: session.meeting_link ?? "",
      status: session.status,
    },
  })

  function handleFormSubmit(values: SessionEditFormValues) {
    onSubmit({
      scheduled_start: fromDateTimeLocalValue(values.scheduled_start),
      meeting_type: values.meeting_type,
      meeting_link: values.meeting_link || null,
      status: values.status,
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
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
          <Label htmlFor="status">Status</Label>
          <Select id="status" aria-invalid={!!errors.status} {...register("status")}>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {SESSION_STATUS_LABELS[status]}
              </option>
            ))}
          </Select>
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

      {submitErrorMessage && <ErrorState title="Couldn't update session" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : "Save Changes"}
      </Button>
    </form>
  )
}
