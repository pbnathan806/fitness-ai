import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Users, CalendarDays, ClipboardCheck, Ruler } from "lucide-react"
import { dashboardService } from "@/services/dashboardService"
import { assignmentService } from "@/services/assignmentService"
import { physicalAssessmentService } from "@/services/physicalAssessmentService"
import { trainerService } from "@/services/trainerService"
import { useDisplayTimezone } from "@/lib/displayTimezone"
import { TodayTomorrowAgendaWidget } from "@/app/pages/dashboard/components/TodayTomorrowAgendaWidget"
import { UpcomingSessionsWidget } from "@/app/pages/dashboard/components/UpcomingSessionsWidget"
import { RecentActivityWidget } from "@/app/pages/dashboard/components/RecentActivityWidget"
import { NeverAssessedWidget } from "@/app/pages/dashboard/components/NeverAssessedWidget"
import { SessionNotesGapWidget } from "@/app/pages/dashboard/components/SessionNotesGapWidget"
import { QuickActionsWidget, type QuickAction } from "@/app/pages/dashboard/components/QuickActionsWidget"

const TRAINER_QUICK_ACTIONS: QuickAction[] = [
  { label: "Assigned Clients", path: "/trainer/clients", icon: Users },
  { label: "Sessions", path: "/trainer/sessions", icon: CalendarDays },
  { label: "Check-ins", path: "/trainer/check-ins", icon: ClipboardCheck },
  { label: "Physical Assessments", path: "/trainer/physical-assessments", icon: Ruler },
]

/** Trainer's own dashboard: Today & Tomorrow's Agenda, Upcoming Sessions,
 * Recent Activity, Session Notes Gap, Never Assessed, and Quick Actions.
 * Client identity is resolved via the trainer's own assigned-clients roster
 * (name only, no PII) rather than GET /clients, consistent with every other
 * trainer-facing screen. Today & Tomorrow's Agenda is the one widget framed
 * in the trainer's own profile timezone rather than the sitewide IST
 * convention - see memory project_deferred_trainer_timezone_framing. */
export function TrainerDashboardPage() {
  const timezone = useDisplayTimezone()

  const clientsQuery = useQuery({
    queryKey: ["assignments", "my-clients"],
    queryFn: assignmentService.getMyClients,
  })

  const agendaQuery = useQuery({
    queryKey: ["trainers", "me", "agenda"],
    queryFn: trainerService.getAgenda,
  })

  const sessionNotesGapQuery = useQuery({
    queryKey: ["trainers", "me", "session-notes-gap"],
    queryFn: trainerService.getSessionNotesGap,
  })

  const sessionsQuery = useQuery({
    queryKey: ["dashboard", "trainer", "upcoming-sessions"],
    queryFn: dashboardService.listSessionsForUpcomingWidget,
  })

  const checkInsQuery = useQuery({
    queryKey: ["dashboard", "trainer", "recent-check-ins"],
    queryFn: dashboardService.listRecentCheckIns,
  })

  const recentPhysicalAssessmentsQuery = useQuery({
    queryKey: ["dashboard", "trainer", "recent-physical-assessments"],
    queryFn: dashboardService.listRecentPhysicalAssessments,
  })

  const allPhysicalAssessmentsQuery = useQuery({
    queryKey: ["physical-assessments", "all"],
    queryFn: physicalAssessmentService.listAllPhysicalAssessments,
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.client_id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const neverAssessedClients = useMemo(() => {
    if (!allPhysicalAssessmentsQuery.data) return undefined
    const assessedClientIds = new Set(allPhysicalAssessmentsQuery.data.map((item) => item.client_id))
    return (clientsQuery.data ?? []).filter((client) => !assessedClientIds.has(client.client_id))
  }, [clientsQuery.data, allPhysicalAssessmentsQuery.data])

  const activityIsLoading = checkInsQuery.isLoading || recentPhysicalAssessmentsQuery.isLoading
  const activityIsError = checkInsQuery.isError || recentPhysicalAssessmentsQuery.isError
  const neverAssessedIsLoading = clientsQuery.isLoading || allPhysicalAssessmentsQuery.isLoading
  const neverAssessedIsError = clientsQuery.isError || allPhysicalAssessmentsQuery.isError

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Trainer Dashboard</h1>
        <p className="text-sm text-muted-foreground">Overview of your assigned clients and activity.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <TodayTomorrowAgendaWidget
            timezone={agendaQuery.data?.timezone}
            sessions={agendaQuery.data?.sessions}
            clientNameById={clientNameById}
            isLoading={agendaQuery.isLoading}
            isError={agendaQuery.isError}
            onRetry={() => agendaQuery.refetch()}
          />
          <UpcomingSessionsWidget
            sessions={sessionsQuery.data}
            clientNameById={clientNameById}
            isLoading={sessionsQuery.isLoading}
            isError={sessionsQuery.isError}
            onRetry={() => sessionsQuery.refetch()}
            description={
              "Your next scheduled sessions, soonest first." +
              (timezone ? ` Times shown in your profile timezone (${timezone}).` : "")
            }
          />
          <RecentActivityWidget
            checkIns={checkInsQuery.data}
            physicalAssessments={recentPhysicalAssessmentsQuery.data}
            clientNameById={clientNameById}
            isLoading={activityIsLoading}
            isError={activityIsError}
            onRetry={() => {
              checkInsQuery.refetch()
              recentPhysicalAssessmentsQuery.refetch()
            }}
            description="Check-ins and physical assessments recently submitted for your clients."
          />
        </div>
        <div className="space-y-4">
          <SessionNotesGapWidget
            gapDays={sessionNotesGapQuery.data?.gap_days}
            timezone={sessionNotesGapQuery.data?.timezone}
            sessions={sessionNotesGapQuery.data?.sessions}
            clientNameById={clientNameById}
            isLoading={sessionNotesGapQuery.isLoading}
            isError={sessionNotesGapQuery.isError}
            onRetry={() => sessionNotesGapQuery.refetch()}
          />
          <NeverAssessedWidget
            clients={neverAssessedClients}
            isLoading={neverAssessedIsLoading}
            isError={neverAssessedIsError}
            onRetry={() => {
              clientsQuery.refetch()
              allPhysicalAssessmentsQuery.refetch()
            }}
          />
          <QuickActionsWidget actions={TRAINER_QUICK_ACTIONS} />
        </div>
      </div>
    </div>
  )
}
