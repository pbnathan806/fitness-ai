import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { UserCog, Star, Trash2, Plus, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDate } from "@/lib/format"
import { getApiErrorMessage } from "@/lib/errors"
import { trainerService } from "@/services/trainerService"
import { assignmentService } from "@/services/assignmentService"
import type { Assignment } from "@/types/assignment"

const LOOKUP_PAGE_SIZE = 100
const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

function toTimeLabel(time: string): string {
  // Backend returns "HH:MM:SS"; drop the seconds for display.
  return time.slice(0, 5)
}

interface TrainerAssignmentCardProps {
  /** Required for variant="full" - the client that new assignments are created for. */
  clientId?: string
  assignments: Assignment[] | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  /** "summary" (Client Details page): count + compact list, no actions.
   * "full" (Manage Trainers page): full list with working assign/remove controls. */
  variant?: "summary" | "full"
}

/** Displays a client's assigned trainers from `GET /assignments` (Task 22.3),
 * and - for variant="full" - lets a SUPER_ADMIN assign/remove trainers via
 * the existing `POST /assignments` and `DELETE /assignments/{id}` endpoints
 * (Task 22.4 added the trainer directory these need; that wiring was left
 * disabled until now). Assigning shows the candidate trainer's weekly
 * availability (`GET /trainers/{id}/availability`) as context only - it's
 * informational, not a hard filter, since real conflicts are enforced when
 * a session is actually scheduled. */
export function TrainerAssignmentCard({
  clientId,
  assignments,
  isLoading,
  isError,
  onRetry,
  variant = "summary",
}: TrainerAssignmentCardProps) {
  const queryClient = useQueryClient()
  const [isAssigning, setIsAssigning] = useState(false)
  const [selectedTrainerId, setSelectedTrainerId] = useState("")
  const [asPrimary, setAsPrimary] = useState(false)
  const [pendingRemovalId, setPendingRemovalId] = useState<string | null>(null)

  const count = assignments?.length ?? 0

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

  const trainerNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const trainer of trainersQuery.data?.items ?? []) {
      map.set(trainer.id, `${trainer.first_name ?? ""} ${trainer.last_name ?? ""}`.trim() || trainer.email)
    }
    return map
  }, [trainersQuery.data])

  const assignedTrainerIds = useMemo(() => new Set((assignments ?? []).map((a) => a.trainer_id)), [assignments])

  const availabilityQuery = useQuery({
    queryKey: ["trainers", selectedTrainerId, "availability"],
    queryFn: () => trainerService.getAvailability(selectedTrainerId),
    enabled: variant === "full" && !!selectedTrainerId,
  })

  const availabilityByWeekday = useMemo(() => {
    const groups = new Map<number, { start_time: string; end_time: string }[]>()
    for (const slot of availabilityQuery.data ?? []) {
      if (!slot.is_available) continue
      const list = groups.get(slot.weekday) ?? []
      list.push({ start_time: slot.start_time, end_time: slot.end_time })
      groups.set(slot.weekday, list)
    }
    return groups
  }, [availabilityQuery.data])

  function resetAssignForm() {
    setIsAssigning(false)
    setSelectedTrainerId("")
    setAsPrimary(false)
  }

  const assignMutation = useMutation({
    mutationFn: () => assignmentService.createAssignment({ client_id: clientId!, trainer_id: selectedTrainerId, is_primary: asPrimary }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] })
      toast.success("Trainer assigned.")
      resetAssignForm()
    },
  })

  const removeMutation = useMutation({
    mutationFn: (assignmentId: string) => assignmentService.deleteAssignment(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] })
      toast.success("Trainer removed.")
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to remove trainer."))
    },
    onSettled: () => setPendingRemovalId(null),
  })

  function handleRemove(assignment: Assignment) {
    const trainerName = trainerNameById.get(assignment.trainer_id) ?? `Trainer #${assignment.trainer_id.slice(0, 8)}`
    const confirmed = window.confirm(`Remove ${trainerName} from this client?`)
    if (confirmed) {
      setPendingRemovalId(assignment.id)
      removeMutation.mutate(assignment.id)
    }
  }

  const assignableTrainers = (trainersQuery.data?.items ?? []).filter((t) => !assignedTrainerIds.has(t.id))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <UserCog className="size-4 text-muted-foreground" aria-hidden="true" />
              Assigned Trainers
            </CardTitle>
            {!isLoading && !isError && <CardDescription>{count} assigned</CardDescription>}
          </div>
          {variant === "full" && !isAssigning && (
            <Button size="sm" onClick={() => setIsAssigning(true)}>
              <Plus className="size-4" />
              Assign Trainer
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {variant === "full" && isAssigning && (
          <div className="space-y-3 rounded-lg border border-border p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Assign a trainer</p>
              <Button variant="ghost" size="icon-sm" aria-label="Cancel" onClick={resetAssignForm}>
                <X className="size-4" />
              </Button>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="assign-trainer-select">Trainer</Label>
              <Select
                id="assign-trainer-select"
                value={selectedTrainerId}
                disabled={trainersQuery.isLoading}
                onChange={(e) => setSelectedTrainerId(e.target.value)}
              >
                <option value="">Select a trainer</option>
                {assignableTrainers.map((trainer) => (
                  <option key={trainer.id} value={trainer.id}>
                    {trainer.first_name} {trainer.last_name} ({trainer.email})
                  </option>
                ))}
              </Select>
              {!trainersQuery.isLoading && assignableTrainers.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  Every active trainer is already assigned to this client.
                </p>
              )}
            </div>

            {selectedTrainerId && (
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">
                  Weekly availability &mdash; context only, not a booking guarantee.
                </p>
                {availabilityQuery.isLoading && <Skeleton className="h-16 w-full" />}
                {!availabilityQuery.isLoading && (availabilityQuery.data?.length ?? 0) === 0 && (
                  <p className="text-xs text-muted-foreground">No availability configured for this trainer.</p>
                )}
                {!availabilityQuery.isLoading && (availabilityQuery.data?.length ?? 0) > 0 && (
                  <ul className="space-y-1 text-xs">
                    {WEEKDAY_LABELS.map((label, weekday) => {
                      const slots = availabilityByWeekday.get(weekday)
                      if (!slots || slots.length === 0) return null
                      return (
                        <li key={weekday} className="flex gap-2">
                          <span className="w-20 shrink-0 font-medium">{label}</span>
                          <span className="text-muted-foreground">
                            {slots.map((s) => `${toTimeLabel(s.start_time)}–${toTimeLabel(s.end_time)}`).join(", ")}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                id="assign-as-primary"
                type="checkbox"
                className="size-4 rounded border-input accent-primary"
                checked={asPrimary}
                onChange={(e) => setAsPrimary(e.target.checked)}
              />
              <Label htmlFor="assign-as-primary" className="cursor-pointer">
                Set as primary trainer
              </Label>
            </div>

            {assignMutation.isError && (
              <ErrorState title="Couldn't assign trainer" message={getApiErrorMessage(assignMutation.error)} />
            )}

            <Button
              size="sm"
              disabled={!selectedTrainerId || assignMutation.isPending}
              onClick={() => assignMutation.mutate()}
            >
              {assignMutation.isPending ? "Assigning..." : "Confirm Assignment"}
            </Button>
          </div>
        )}

        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && (
          <ErrorState message="Unable to load trainer assignments." onRetry={onRetry} />
        )}

        {!isLoading && !isError && count === 0 && <EmptyState icon={UserCog} message="No trainers assigned." />}

        {!isLoading && !isError && count > 0 && (
          <ul className="divide-y">
            {assignments!.map((assignment) => (
              <li key={assignment.id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium" title={assignment.trainer_id}>
                    {trainerNameById.get(assignment.trainer_id) ?? `Trainer #${assignment.trainer_id.slice(0, 8)}`}
                  </p>
                  <p className="text-xs text-muted-foreground">Assigned {formatDate(assignment.assigned_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  {assignment.is_primary && (
                    <Badge variant="default">
                      <Star className="size-3" />
                      Primary
                    </Badge>
                  )}
                  {variant === "full" && (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      disabled={removeMutation.isPending && pendingRemovalId === assignment.id}
                      aria-label="Remove trainer"
                      onClick={() => handleRemove(assignment)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
