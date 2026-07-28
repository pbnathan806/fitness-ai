import { ClipboardList } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import type { TrainerSummary } from "@/types/trainer"

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  )
}

interface TrainerSummaryCardProps {
  summary: TrainerSummary | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

/** Summary section of the Trainer Details page (Task 22.4.1), backed by the
 * real `GET /trainers/{id}/summary` endpoint. */
export function TrainerSummaryCard({ summary, isLoading, isError, onRetry }: TrainerSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="size-4 text-muted-foreground" aria-hidden="true" />
          Summary
        </CardTitle>
        <CardDescription>Current workload snapshot</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && <ErrorState message="Unable to load summary data." onRetry={onRetry} />}

        {!isLoading && !isError && summary && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <Stat label="Assigned Clients" value={summary.assigned_clients} />
            <Stat label="Sessions This Week" value={summary.sessions_this_week} />
            <Stat label="Completed Sessions This Month" value={summary.completed_sessions_this_month} />
            <Stat label="Pending Check-ins" value={summary.pending_check_ins} />
            <Stat label="Pending Measurements" value={summary.pending_measurements} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
