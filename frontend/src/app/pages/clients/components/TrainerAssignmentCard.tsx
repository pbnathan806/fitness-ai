import { UserCog, Star, Trash2, Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDate } from "@/lib/format"
import type { Assignment } from "@/types/assignment"

const TRAINER_DIRECTORY_NOTE =
  "Trainer directory API is not yet available. This functionality will be enabled when the corresponding backend API becomes available."

interface TrainerAssignmentCardProps {
  assignments: Assignment[] | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  /** "summary" (Client Details page): count + compact list, no actions.
   * "full" (Manage Trainers page): full list with disabled assign/remove controls. */
  variant?: "summary" | "full"
}

/** Displays a client's assigned trainers from the existing `GET /assignments`
 * API (Task 22.3). There is no trainer-directory endpoint, so trainers are
 * shown by id only (no name/email available) and Assign/Remove stay disabled
 * until the backend adds one - Task 22.4 confirmed no such endpoint exists. */
export function TrainerAssignmentCard({
  assignments,
  isLoading,
  isError,
  onRetry,
  variant = "summary",
}: TrainerAssignmentCardProps) {
  const count = assignments?.length ?? 0

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
          {variant === "full" && (
            <Button size="sm" disabled title={TRAINER_DIRECTORY_NOTE}>
              <Plus className="size-4" />
              Assign Trainer
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {variant === "full" && <p className="text-xs text-muted-foreground">{TRAINER_DIRECTORY_NOTE}</p>}

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
                    Trainer #{assignment.trainer_id.slice(0, 8)}
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
                      disabled
                      title={TRAINER_DIRECTORY_NOTE}
                      aria-label="Remove trainer"
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
