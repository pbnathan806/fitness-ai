import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Plus, CalendarRange } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SessionTable, type SessionRow } from "@/app/pages/sessions/components/SessionTable"
import { SessionFilters } from "@/app/pages/sessions/components/SessionFilters"
import { toLocalDateValue } from "@/app/pages/sessions/components/dateTimeLocal"
import { sessionService } from "@/services/sessionService"
import { clientService } from "@/services/clientService"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SessionMeetingType, SessionStatus } from "@/types/session"

const PAGE_SIZE = 10
const LOOKUP_PAGE_SIZE = 100

export function SessionsListPage() {
  const [statusFilter, setStatusFilter] = useState<SessionStatus | "ALL">("ALL")
  const [meetingTypeFilter, setMeetingTypeFilter] = useState<SessionMeetingType | "ALL">("ALL")
  const [dateFilter, setDateFilter] = useState("")
  const [page, setPage] = useState(1)

  const sessionsQuery = useQuery({ queryKey: ["sessions", "all"], queryFn: sessionService.listAllSessions })
  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })
  const trainersQuery = useQuery({
    queryKey: ["trainers", "lookup"],
    queryFn: () =>
      trainerService.listTrainers({ page: 1, page_size: LOOKUP_PAGE_SIZE, sort_by: "first_name", sort_dir: "asc" }),
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const trainerNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const trainer of trainersQuery.data?.items ?? []) {
      map.set(trainer.id, `${trainer.first_name ?? ""} ${trainer.last_name ?? ""}`.trim() || trainer.email)
    }
    return map
  }, [trainersQuery.data])

  const filteredRows = useMemo<SessionRow[]>(() => {
    return (sessionsQuery.data ?? [])
      .filter((s) => statusFilter === "ALL" || s.status === statusFilter)
      .filter((s) => meetingTypeFilter === "ALL" || s.meeting_type === meetingTypeFilter)
      .filter((s) => !dateFilter || toLocalDateValue(s.scheduled_start) === dateFilter)
      .map((session) => ({
        session,
        clientName: clientNameById.get(session.client_id) ?? `Client #${session.client_id.slice(0, 8)}`,
        trainerName: trainerNameById.get(session.trainer_id) ?? `Trainer #${session.trainer_id.slice(0, 8)}`,
      }))
  }, [sessionsQuery.data, statusFilter, meetingTypeFilter, dateFilter, clientNameById, trainerNameById])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageRows = filteredRows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const isLoading = sessionsQuery.isLoading || clientsQuery.isLoading || trainersQuery.isLoading
  const isError = sessionsQuery.isError

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Sessions</h1>
          <p className="text-sm text-muted-foreground">Manage coaching sessions across all clients and trainers.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" render={<Link to="/super-admin/sessions/bulk" />} nativeButton={false}>
            <CalendarRange className="size-4" />
            Bulk Create
          </Button>
          <Button render={<Link to="/super-admin/sessions/new" />} nativeButton={false}>
            <Plus className="size-4" />
            New Session
          </Button>
        </div>
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
        basePath="/super-admin/sessions"
      />
    </div>
  )
}
