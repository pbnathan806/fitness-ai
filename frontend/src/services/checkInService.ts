import { apiClient } from "@/services/apiClient"
import type { CheckIn } from "@/types/checkIn"

export const checkInService = {
  async getClientCheckIns(clientId: string): Promise<CheckIn[]> {
    const { data } = await apiClient.get<CheckIn[]>(`/check-ins/client/${clientId}`)
    return data
  },
}
