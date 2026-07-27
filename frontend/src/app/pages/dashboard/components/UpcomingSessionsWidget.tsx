import { CalendarClock, Video, Phone, MapPin, MessageCircle } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { formatDateTime } from "@/lib/format"
import type { DashboardSession } from "@/types/dashboard"

const MEETING_ICONS: Record<string, LucideIcon> = {
  GOOGLE_MEET: Video,
  ZOOM: Video,
  WHATSAPP: MessageCircle,
  PHONE: Phone,
  IN_PERSON: MapPin,
}

interface UpcomingSessionsWidgetProps {
  sessions: DashboardSession[] | undefined
  clientNameById: Map<string, string>
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

const MAX_ITEMS = 10

export function UpcomingSessionsWidget({
  sessions,
  clientNameById,
  isLoading,
  isError,
  onRetry,
}: UpcomingSessionsWidgetProps) {
  const upcoming = sessions
    ? sessions
        .filter((session) => session.status !== "CANCELLED" && new Date(session.scheduled_start) >= new Date())
        .sort((a, b) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime())
        .slice(0, MAX_ITEMS)
    : []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="size-4 text-muted-foreground" aria-hidden="true" />
          Upcoming Sessions
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

        {!isLoading && isError && (
          <ErrorState message="Couldn't load upcoming sessions." onRetry={onRetry} />
        )}

        {!isLoading && !isError && upcoming.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">No upcoming sessions scheduled.</p>
        )}

        {!isLoading && !isError && upcoming.length > 0 && (
          <ul className="divide-y">
            {upcoming.map((session) => {
              const Icon = MEETING_ICONS[session.meeting_type] ?? CalendarClock
              return (
                <li key={session.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                  <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {clientNameById.get(session.client_id) ?? "Client"}
                    </p>
                    <p className="text-xs text-muted-foreground">{formatDateTime(session.scheduled_start)}</p>
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
