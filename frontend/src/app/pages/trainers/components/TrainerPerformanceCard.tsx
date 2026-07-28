import { BarChart3 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import type { TrainerPerformance } from "@/types/trainer"

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  )
}

interface TrainerPerformanceCardProps {
  performance: TrainerPerformance | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

/** Performance section of the Trainer Details page (Task 22.4.1), backed by
 * the real `GET /trainers/{id}/performance` endpoint. */
export function TrainerPerformanceCard({ performance, isLoading, isError, onRetry }: TrainerPerformanceCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="size-4 text-muted-foreground" aria-hidden="true" />
          Performance
        </CardTitle>
        <CardDescription>Completion and engagement rates</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && <ErrorState message="Unable to load performance data." onRetry={onRetry} />}

        {!isLoading && !isError && performance && (
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Completion Rate" value={`${performance.completion_rate}%`} />
            <Stat label="Average Check-in Rate" value={`${performance.average_check_in_rate}%`} />
            <Stat label="Assigned Clients" value={performance.assigned_clients} />
            <Stat label="Completed Sessions" value={performance.completed_sessions} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
