import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { SessionTable, type SessionRow } from "@/app/pages/sessions/components/SessionTable"
import { SessionFilters } from "@/app/pages/sessions/components/SessionFilters"
import { toLocalDateValue } from "@/app/pages/sessions/components/dateTimeLocal"
import { sessionService } from "@/services/sessionService"
import { clientService } from "@/services/clientService"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SessionMeetingType, SessionStatus } from "@/types/session"

const PAGE_SIZE = 10

/** Trainer's own Sessions list (Task 22.6). `GET /sessions` is already
 * scoped server-side to the caller's own sessions for the TRAINER role
 * (SessionService.list_sessions), so this reuses sessionService.listAllSessions
 * as-is - no client-scoping needed here beyond what the backend already does. */
export function TrainerSessionsListPage() {
  const [statusFilter, setStatusFilter] = useState<SessionStatus | "ALL">("ALL")
  const [meetingTypeFilter, setMeetingTypeFilter] = useState<SessionMeetingType | "ALL">("ALL")
  const [dateFilter, setDateFilter] = useState("")
  const [page, setPage] = useState(1)

  const sessionsQuery = useQuery({ queryKey: ["sessions", "all"], queryFn: sessionService.listAllSessions })
  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })
  const selfQuery = useQuery({ queryKey: ["trainers", "me"], queryFn: trainerService.getSelf })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const selfName = selfQuery.data
    ? `${selfQuery.data.first_name ?? ""} ${selfQuery.data.last_name ?? ""}`.trim() || selfQuery.data.email
    : "You"

  const filteredRows = useMemo<SessionRow[]>(() => {
    return (sessionsQuery.data ?? [])
      .filter((s) => statusFilter === "ALL" || s.status === statusFilter)
      .filter((s) => meetingTypeFilter === "ALL" || s.meeting_type === meetingTypeFilter)
      .filter((s) => !dateFilter || toLocalDateValue(s.scheduled_start) === dateFilter)
      .map((session) => ({
        session,
        clientName: clientNameById.get(session.client_id) ?? `Client #${session.client_id.slice(0, 8)}`,
        trainerName: selfName,
      }))
  }, [sessionsQuery.data, statusFilter, meetingTypeFilter, dateFilter, clientNameById, selfName])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = filteredRows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const isLoading = sessionsQuery.isLoading || clientsQuery.isLoading || selfQuery.isLoading
  const isError = sessionsQuery.isError

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Sessions</h1>
        <p className="text-sm text-muted-foreground">Your scheduled coaching sessions.</p>
      </div>

      <SessionFilters
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => {
          setStatusFilter(v)
          setPage(1)
        }}
        meetingTypeFilter={meetingTypeFilter}
        onMeetingTypeFilterChange={(v) => {
          setMeetingTypeFilter(v)
          setPage(1)
        }}
        dateFilter={dateFilter}
        onDateFilterChange={(v) => {
          setDateFilter(v)
          setPage(1)
        }}
        errorMessage={isError ? getApiErrorMessage(sessionsQuery.error, "Unable to load sessions.") : null}
      />

      <SessionTable
        rows={pageRows}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => sessionsQuery.refetch()}
        page={currentPage}
        totalPages={totalPages}
        onPageChange={setPage}
        basePath="/trainer/sessions"
      />
    </div>
  )
}
