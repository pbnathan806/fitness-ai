import { isAxiosError } from "axios"
import { apiClient } from "@/services/apiClient"
import type { CheckIn, CheckInCreateInput, CheckInUpdateInput } from "@/types/checkIn"
import type { PendingCheckIn } from "@/types/dashboard"

export const checkInService = {
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
