import { CalendarClock, Video, Phone, MapPin, MessageCircle } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import type { TrainerAgendaSession } from "@/types/trainer"

const MEETING_ICONS: Record<string, LucideIcon> = {
  GOOGLE_MEET: Video,
  ZOOM: Video,
  WHATSAPP: MessageCircle,
  PHONE: Phone,
  IN_PERSON: MapPin,
}

interface TodayTomorrowAgendaWidgetProps {
  timezone: string | undefined
  sessions: TrainerAgendaSession[] | undefined
  clientNameById: Map<string, string>
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

/** Formats a session time in the trainer's own profile timezone - not the
 * viewer's browser-local timezone that formatDateTime() uses elsewhere -
 * so the displayed clock time always matches the "Today"/"Tomorrow" bucket
 * the backend computed it into. */
function formatTimeInZone(iso: string, timezone: string): string {
  return new Intl.DateTimeFormat(undefined, { timeStyle: "short", timeZone: timezone }).format(new Date(iso))
}

export function TodayTomorrowAgendaWidget({
  timezone,
  sessions,
  clientNameById,
  isLoading,
  isError,
  onRetry,
}: TodayTomorrowAgendaWidgetProps) {
  const today = sessions?.filter((s) => s.day === "today") ?? []
  const tomorrow = sessions?.filter((s) => s.day === "tomorrow") ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="size-4 text-muted-foreground" aria-hidden="true" />
          Today & Tomorrow's Agenda
        </CardTitle>
        <CardDescription>
          Your sessions for today and tomorrow.
          {timezone && ` Times shown in your profile timezone (${timezone}).`}
        </CardDescription>
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
          <ErrorState message="Couldn't load your agenda." onRetry={onRetry} />
        )}

        {!isLoading && !isError && today.length === 0 && tomorrow.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No sessions scheduled for today or tomorrow.
          </p>
        )}

        {!isLoading && !isError && (today.length > 0 || tomorrow.length > 0) && timezone && (
          <div className="space-y-4">
            {[
              { label: "Today", items: today },
              { label: "Tomorrow", items: tomorrow },
            ]
              .filter((group) => group.items.length > 0)
              .map((group) => (
                <div key={group.label}>
                  <h3 className="mb-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    {group.label}
                  </h3>
                  <ul className="divide-y">
                    {group.items.map((session) => {
                      const Icon = MEETING_ICONS[session.meeting_type] ?? CalendarClock
                      return (
                        <li key={session.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                          <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">
                              {clientNameById.get(session.client_id) ?? "Client"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatTimeInZone(session.scheduled_start, timezone)}
                            </p>
                          </div>
                          {session.status === "RESCHEDULED" && (
                            <Badge variant="outline" className="shrink-0 text-xs">
                              Rescheduled
                            </Badge>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
