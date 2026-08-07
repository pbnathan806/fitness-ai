import { Activity, ClipboardCheck, Ruler } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { formatRelativeToNow } from "@/lib/format"
import type { DashboardCheckIn, DashboardPhysicalAssessment } from "@/types/dashboard"

interface RecentActivityWidgetProps {
  checkIns: DashboardCheckIn[] | undefined
  physicalAssessments: DashboardPhysicalAssessment[] | undefined
  clientNameById: Map<string, string>
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

const MAX_ITEMS = 8

export function RecentActivityWidget({
  checkIns,
  physicalAssessments,
  clientNameById,
  isLoading,
  isError,
  onRetry,
}: RecentActivityWidgetProps) {
  const feed = [
    ...(checkIns ?? []).map((item) => ({
      id: item.id,
      kind: "check-in" as const,
      clientName: clientNameById.get(item.client_id) ?? "Client",
      timestamp: item.submitted_at,
    })),
    ...(physicalAssessments ?? []).map((item) => ({
      id: item.id,
      kind: "physical-assessment" as const,
      clientName: clientNameById.get(item.client_id) ?? "Client",
      timestamp: item.recorded_at,
    })),
  ]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, MAX_ITEMS)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="size-4 text-muted-foreground" aria-hidden="true" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && <ErrorState message="Couldn't load recent activity." onRetry={onRetry} />}

        {!isLoading && !isError && feed.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">No recent activity yet.</p>
        )}

        {!isLoading && !isError && feed.length > 0 && (
          <ul className="divide-y">
            {feed.map((item) => {
              const Icon = item.kind === "check-in" ? ClipboardCheck : Ruler
              const description = item.kind === "check-in" ? "submitted a check-in" : "recorded a physical assessment"
              return (
                <li key={`${item.kind}-${item.id}`} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                  <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm">
                      <span className="font-medium">{item.clientName}</span> {description}
                    </p>
                    <p className="text-xs text-muted-foreground">{formatRelativeToNow(item.timestamp)}</p>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
