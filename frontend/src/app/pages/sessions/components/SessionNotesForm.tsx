import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ErrorState } from "@/components/common/ErrorState"
import type { Session, SessionNotesUpdateInput } from "@/types/session"

const schema = z.object({
  trainer_notes: z.string().optional().or(z.literal("")),
  trainer_feedback: z.string().optional().or(z.literal("")),
  homework: z.string().optional().or(z.literal("")),
  next_session_focus: z.string().optional().or(z.literal("")),
})

type SessionNotesFormValues = z.infer<typeof schema>

interface SessionNotesFormProps {
  session: Session
  onSubmit: (values: SessionNotesUpdateInput) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
}

/** Session Notes form (Task 22.6 requirement 7) - trainer_notes,
 * trainer_feedback, homework, next_session_focus via `PATCH
 * /sessions/{id}/notes`. Shared by SUPER_ADMIN and TRAINER session detail
 * screens; never rendered for CLIENT. */
export function SessionNotesForm({ session, onSubmit, isSubmitting, submitErrorMessage }: SessionNotesFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SessionNotesFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SessionNotesFormValues>,
    values: {
      trainer_notes: session.trainer_notes ?? "",
      trainer_feedback: session.trainer_feedback ?? "",
      homework: session.homework ?? "",
      next_session_focus: session.next_session_focus ?? "",
    },
  })

  function handleFormSubmit(values: SessionNotesFormValues) {
    onSubmit({
      trainer_notes: values.trainer_notes || null,
      trainer_feedback: values.trainer_feedback || null,
      homework: values.homework || null,
      next_session_focus: values.next_session_focus || null,
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="trainer_notes">Trainer Notes</Label>
        <Textarea id="trainer_notes" aria-invalid={!!errors.trainer_notes} {...register("trainer_notes")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="trainer_feedback">Trainer Feedback</Label>
        <Textarea id="trainer_feedback" aria-invalid={!!errors.trainer_feedback} {...register("trainer_feedback")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="homework">Homework</Label>
        <Textarea id="homework" aria-invalid={!!errors.homework} {...register("homework")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="next_session_focus">Next Session Focus</Label>
        <Textarea id="next_session_focus" aria-invalid={!!errors.next_session_focus} {...register("next_session_focus")} />
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't update session notes" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : "Save Notes"}
      </Button>
    </form>
  )
}
