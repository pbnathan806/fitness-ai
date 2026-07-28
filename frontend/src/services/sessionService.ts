import { apiClient } from "@/services/apiClient"
import type {
  ClientSessionView,
  PaginatedSessions,
  Session,
  SessionAttendanceUpdateInput,
  SessionBulkCreateInput,
  SessionBulkCreateResult,
  SessionCreateInput,
  SessionNotesUpdateInput,
  SessionUpdateInput,
} from "@/types/session"

// `GET /sessions` has no status/meeting-type/date query params, so (as in
// subscriptionService.listAllSubscriptions / clientService.listAllClients)
// the Sessions list pages walk every page once, bounded by LIST_ALL_MAX_PAGES,
// and filter/paginate in the browser. This also transparently covers TRAINER
// callers, since the backend already scopes `GET /sessions` to the caller's
// own sessions for that role.
const LIST_ALL_PAGE_SIZE = 100
const LIST_ALL_MAX_PAGES = 50

function toClientView(session: Session): ClientSessionView {
  const { trainer_notes: _trainer_notes, trainer_feedback: _trainer_feedback, next_session_focus: _next_session_focus, ...rest } = session
  return rest
}

export const sessionService = {
  async listSessions(page: number, pageSize: number): Promise<PaginatedSessions> {
    const { data } = await apiClient.get<PaginatedSessions>("/sessions", {
      params: { page, page_size: pageSize },
    })
    return data
  },

  /** Calls `sessionService.listSessions` (not `this.listSessions`) since this
   * is passed around as a bare function reference (e.g. react-query
   * `queryFn`), which would otherwise lose its `this` binding. */
  async listAllSessions(): Promise<Session[]> {
    const first = await sessionService.listSessions(1, LIST_ALL_PAGE_SIZE)
    const totalPages = Math.min(first.total_pages, LIST_ALL_MAX_PAGES)
    if (totalPages <= 1) return first.items

    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => sessionService.listSessions(i + 2, LIST_ALL_PAGE_SIZE)),
    )
    return [first.items, ...rest.map((page) => page.items)].flat()
  },

  async getSession(sessionId: string): Promise<Session> {
    const { data } = await apiClient.get<Session>(`/sessions/${sessionId}`)
    return data
  },

  async createSession(payload: SessionCreateInput): Promise<Session> {
    const { data } = await apiClient.post<Session>("/sessions", payload)
    return data
  },

  async bulkCreateSessions(payload: SessionBulkCreateInput): Promise<SessionBulkCreateResult> {
    const { data } = await apiClient.post<SessionBulkCreateResult>("/sessions/bulk", payload)
    return data
  },

  async updateSession(sessionId: string, payload: SessionUpdateInput): Promise<Session> {
    const { data } = await apiClient.patch<Session>(`/sessions/${sessionId}`, payload)
    return data
  },

  async updateSessionNotes(sessionId: string, payload: SessionNotesUpdateInput): Promise<Session> {
    const { data } = await apiClient.patch<Session>(`/sessions/${sessionId}/notes`, payload)
    return data
  },

  async updateSessionAttendance(sessionId: string, payload: SessionAttendanceUpdateInput): Promise<Session> {
    const { data } = await apiClient.patch<Session>(`/sessions/${sessionId}/attendance`, payload)
    return data
  },

  /** `GET /sessions/my-sessions` - CLIENT only. The backend's `SessionResponse`
   * technically still carries trainer_notes/trainer_feedback/next_session_focus,
   * but Task 22.6 requires the Client UI to never expose them, so every
   * session is narrowed to `ClientSessionView` right here at the service
   * boundary before it reaches any component. */
  async getMySessions(): Promise<ClientSessionView[]> {
    const { data } = await apiClient.get<Session[]>("/sessions/my-sessions")
    return data.map(toClientView)
  },

  /** Single-session counterpart to `getMySessions`, for the Client session
   * details screen. Uses `GET /sessions/{id}` (permitted for CLIENT on their
   * own sessions per SessionService.get_session) and applies the same
   * field-narrowing. */
  async getMySessionDetail(sessionId: string): Promise<ClientSessionView> {
    const session = await sessionService.getSession(sessionId)
    return toClientView(session)
  },
}
