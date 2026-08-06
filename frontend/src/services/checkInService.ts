import { isAxiosError } from "axios"
import { apiClient } from "@/services/apiClient"
import type { CheckIn, CheckInCreateInput, CheckInUpdateInput, PaginatedCheckIns } from "@/types/checkIn"
import type { PendingCheckIn } from "@/types/dashboard"

// `GET /check-ins` has no filter params, so (as in sessionService.listAllSessions)
// every page is walked once, bounded by LIST_ALL_MAX_PAGES, and the backend
// already scopes the results to the caller's own assigned clients for TRAINER.
const LIST_ALL_PAGE_SIZE = 100
const LIST_ALL_MAX_PAGES = 50

export const checkInService = {
  async listCheckIns(page: number, pageSize: number): Promise<PaginatedCheckIns> {
    const { data } = await apiClient.get<PaginatedCheckIns>("/check-ins", {
      params: { page, page_size: pageSize },
    })
    return data
  },

  /** Calls `checkInService.listCheckIns` (not `this.listCheckIns`) since this
   * is passed around as a bare function reference (e.g. react-query
   * `queryFn`), which would otherwise lose its `this` binding. */
  async listAllCheckIns(): Promise<CheckIn[]> {
    const first = await checkInService.listCheckIns(1, LIST_ALL_PAGE_SIZE)
    const totalPages = Math.min(first.total_pages, LIST_ALL_MAX_PAGES)
    if (totalPages <= 1) return first.items

    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => checkInService.listCheckIns(i + 2, LIST_ALL_PAGE_SIZE)),
    )
    return [first.items, ...rest.map((page) => page.items)].flat()
  },

  async getClientCheckIns(clientId: string): Promise<CheckIn[]> {
    const { data } = await apiClient.get<CheckIn[]>(`/check-ins/client/${clientId}`)
    return data
  },

  /** Returns null when no check-in exists yet for this session (404) rather
   * than throwing, so callers can render a "Submit Check-in" form instead of
   * an error state for the common case. */
  async getBySession(sessionId: string): Promise<CheckIn | null> {
    try {
      const { data } = await apiClient.get<CheckIn>(`/check-ins/session/${sessionId}`)
      return data
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) return null
      throw error
    }
  },

  async create(input: CheckInCreateInput): Promise<CheckIn> {
    const { data } = await apiClient.post<CheckIn>("/check-ins", input)
    return data
  },

  async update(checkInId: string, input: CheckInUpdateInput): Promise<CheckIn> {
    const { data } = await apiClient.patch<CheckIn>(`/check-ins/${checkInId}`, input)
    return data
  },

  /** TRAINER/SUPER_ADMIN only - CLIENT gets 403 (clients have no pending-check-ins
   * queue; their Session Details screen shows a simple Submitted/Not Submitted
   * status instead). */
  async listPending(): Promise<PendingCheckIn[]> {
    const { data } = await apiClient.get<PendingCheckIn[]>("/check-ins/pending")
    return data
  },
}
