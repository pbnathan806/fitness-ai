import { Link } from "react-router-dom"
import { Ruler, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import type { AssignedClient } from "@/types/assignment"

interface NeverAssessedWidgetProps {
  /** Assigned clients with zero physical assessment records - already
   * filtered down to just this set by the caller (TrainerDashboardPage),
   * same client-side diff used on the Physical Assessments page's Never
   * Assessed tab. */
  clients: AssignedClient[] | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

const MAX_ITEMS = 6

/** Surfaces assigned clients who have never had a single physical
 * assessment recorded - a client that's invisible to the Pending queue
 * (which only tracks clients with an existing-but-stale record) and to
 * Recent Activity (nothing has ever happened for them yet). */
export function NeverAssessedWidget({ clients, isLoading, isError, onRetry }: NeverAssessedWidgetProps) {
  const shown = (clients ?? []).slice(0, MAX_ITEMS)
  const remaining = (clients?.length ?? 0) - shown.length

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Ruler className="size-4 text-muted-foreground" aria-hidden="true" />
            Never Assessed
          </CardTitle>
          {!isLoading && !isError && clients && (
            <Badge variant={clients.length > 0 ? "warning" : "secondary"}>{clients.length}</Badge>
          )}
        </div>
        <CardDescription>Assigned clients who have never had a physical assessment recorded.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && <ErrorState message="Couldn't load clients." onRetry={onRetry} />}

        {!isLoading && !isError && shown.length === 0 && (
          <p className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            Every assigned client has at least one physical assessment on record.
          </p>
        )}

        {!isLoading && !isError && shown.length > 0 && (
          <ul className="divide-y">
            {shown.map((client) => (
              <li key={client.assignment_id} className="py-2 text-sm first:pt-0 last:pb-0">
                {client.first_name} {client.last_name}
              </li>
            ))}
          </ul>
        )}

        {!isLoading && !isError && (shown.length > 0 || remaining > 0) && (
          <Link
            to="/trainer/physical-assessments"
            className="mt-3 inline-block text-sm font-medium text-primary hover:underline"
          >
            {remaining > 0 ? `View all ${clients?.length} in Physical Assessments →` : "Add a physical assessment →"}
          </Link>
        )}
      </CardContent>
    </Card>
  )
}
