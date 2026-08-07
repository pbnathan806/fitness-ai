import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { CheckInForm } from "@/app/pages/sessions/components/CheckInForm"
import { checkInService } from "@/services/checkInService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import type { CheckInCreateInput, CheckInUpdateInput } from "@/types/checkIn"
import type { Session } from "@/types/session"

const EDIT_WINDOW_EXPIRED_MESSAGE =
  "This check-in can no longer be modified. The configured edit window has expired."

interface SessionCheckInCardProps {
  /** Only id/scheduled_start/status are read, so this accepts both the full
   * Session (TRAINER/SUPER_ADMIN) and the narrower ClientSessionView (CLIENT). */
  session: Pick<Session, "id" | "scheduled_start" | "status">
  /** Whether this role may submit a brand-new check-in for this session.
   * CLIENT, TRAINER, and SUPER_ADMIN may all submit, per the RBAC spec's
   * "Client Check-ins" row (Yes for all three roles) and the backend, which
   * permits SUPER_ADMIN unconditionally (`CheckInService._authorize`). */
  allowSubmit: boolean
  /** When provided, an extra "Submitted By" row is shown (SUPER_ADMIN's audit
   * view), resolving the check-in's submitted_by user id to a display label.
   * Omitted for CLIENT/TRAINER, who already know who submitted it. */
  resolveSubmittedBy?: (submittedByUserId: string) => string
}

/** Check-in section of a Session Details page - shared by CLIENT, TRAINER,
 * and SUPER_ADMIN screens, which differ only in whether Submit is offered.
 * The edit window's length is an application setting only SUPER_ADMIN can
 * read, so rather than predicting expiry client-side, edits are always
 * attempted and a 409 flips the card into a locked state showing the exact
 * message the product spec requires. */
export function SessionCheckInCard({ session, allowSubmit, resolveSubmittedBy }: SessionCheckInCardProps) {
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [editWindowExpired, setEditWindowExpired] = useState(false)

  const checkInQuery = useQuery({
    queryKey: ["check-ins", "session", session.id],
    queryFn: () => checkInService.getBySession(session.id),
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["check-ins", "session", session.id] })
  }

  const createMutation = useMutation({
    mutationFn: (values: CheckInUpdateInput) =>
      checkInService.create({ session_id: session.id, ...values } as CheckInCreateInput),
    onSuccess: (created) => {
      queryClient.setQueryData(["check-ins", "session", session.id], created)
      invalidate()
      toast.success("Check-in submitted.")
    },
  })

  const updateMutation = useMutation({
    mutationFn: (values: CheckInUpdateInput) => checkInService.update(checkInQuery.data!.id, values),
    onSuccess: (updated) => {
      queryClient.setQueryData(["check-ins", "session", session.id], updated)
      invalidate()
      setIsEditing(false)
      toast.success("Check-in updated.")
    },
    onError: (error) => {
      if (getApiErrorMessage(error) === EDIT_WINDOW_EXPIRED_MESSAGE) {
        setEditWindowExpired(true)
        setIsEditing(false)
      }
    },
  })

  if (checkInQuery.isLoading) {
    return <LoadingSpinner label="Loading check-in..." className="py-8" />
  }

  if (checkInQuery.isError) {
    return (
      <ErrorState
        title="Unable to load check-in"
        message={getApiErrorMessage(checkInQuery.error)}
        onRetry={() => checkInQuery.refetch()}
      />
    )
  }

  const checkIn = checkInQuery.data
  const now = new Date()
  const sessionStarted = new Date(session.scheduled_start) <= now
  const sessionCancelled = session.status === "CANCELLED"

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Check-in</CardTitle>
          <Badge variant={checkIn ? "success" : "secondary"}>
            {checkIn ? "Check-in Submitted" : "Check-in Not Submitted"}
          </Badge>
        </div>
        <CardDescription>The client's progress since the previous coaching session.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {checkIn && !isEditing && (
          <>
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-foreground">Sleep (hours)</dt>
                <dd className="text-sm font-medium">{checkIn.sleep_hours ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Water Intake (liters)</dt>
                <dd className="text-sm font-medium">{checkIn.water_intake_liters ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Energy Level</dt>
                <dd className="text-sm font-medium">{checkIn.energy_level ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Mood</dt>
                <dd className="text-sm font-medium">{checkIn.mood ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Workout Completed</dt>
                <dd className="text-sm font-medium">
                  {checkIn.workout_completed === null ? "—" : checkIn.workout_completed ? "Yes" : "No"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Diet Followed</dt>
                <dd className="text-sm font-medium">
                  {checkIn.diet_followed === null ? "—" : checkIn.diet_followed ? "Yes" : "No"}
                </dd>
              </div>
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-xs text-muted-foreground">Notes</dt>
                <dd className="text-sm font-medium whitespace-pre-wrap">{checkIn.notes || "—"}</dd>
              </div>
              {resolveSubmittedBy && (
                <div>
                  <dt className="text-xs text-muted-foreground">Submitted By</dt>
                  <dd className="text-sm font-medium">{resolveSubmittedBy(checkIn.submitted_by)}</dd>
                </div>
              )}
              <div>
                <dt className="text-xs text-muted-foreground">Submitted At</dt>
                <dd className="text-sm font-medium">{formatDateTime(checkIn.submitted_at)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Last Updated At</dt>
                <dd className="text-sm font-medium">{formatDateTime(checkIn.updated_at)}</dd>
              </div>
            </dl>

            {editWindowExpired ? (
              <ErrorState title="Edit window expired" message={EDIT_WINDOW_EXPIRED_MESSAGE} />
            ) : (
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                Edit Check-in
              </Button>
            )}
          </>
        )}

        {checkIn && isEditing && (
          <CheckInForm
            checkIn={checkIn}
            onSubmit={(values) => updateMutation.mutate(values)}
            isSubmitting={updateMutation.isPending}
            submitErrorMessage={
              updateMutation.isError && getApiErrorMessage(updateMutation.error) !== EDIT_WINDOW_EXPIRED_MESSAGE
                ? getApiErrorMessage(updateMutation.error)
                : null
            }
            submitLabel="Save Check-in"
          />
        )}

        {!checkIn && allowSubmit && sessionCancelled && (
          <p className="text-sm text-muted-foreground">Check-ins cannot be submitted for a cancelled session.</p>
        )}

        {!checkIn && allowSubmit && !sessionCancelled && !sessionStarted && (
          <p className="text-sm text-muted-foreground">
            The check-in can be submitted once this session has started.
          </p>
        )}

        {!checkIn && allowSubmit && !sessionCancelled && sessionStarted && (
          <CheckInForm
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Submit Check-in"
          />
        )}
      </CardContent>
    </Card>
  )
}
