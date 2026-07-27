import { isAxiosError } from "axios"
import { apiClient } from "@/services/apiClient"
import type { LatestMeasurement } from "@/types/measurement"

export const measurementService = {
  /** Returns null when the client has no measurements yet (backend 404s in that case). */
  async getLatestMeasurement(clientId: string): Promise<LatestMeasurement | null> {
    try {
      const { data } = await apiClient.get<LatestMeasurement>(`/measurements/client/${clientId}/latest`)
      return data
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  },
}
