import { isAxiosError } from "axios"
import { apiClient } from "@/services/apiClient"
import type {
  LatestMeasurement,
  Measurement,
  MeasurementCreateInput,
  MeasurementUpdateInput,
  PaginatedMeasurements,
  PendingMeasurement,
} from "@/types/measurement"

export const measurementService = {
  /** Server-paginated list across all clients (SUPER_ADMIN), assigned
   * clients (TRAINER), or own records (CLIENT) - see backend
   * MeasurementService.list_measurements. */
  async list(page: number, pageSize: number): Promise<PaginatedMeasurements> {
    const { data } = await apiClient.get<PaginatedMeasurements>("/measurements", {
      params: { page, page_size: pageSize },
    })
    return data
  },

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

  /** Full history for a client, newest first. */
  async getClientMeasurements(clientId: string): Promise<Measurement[]> {
    const { data } = await apiClient.get<Measurement[]>(`/measurements/client/${clientId}`)
    return data
  },

  async getMeasurement(measurementId: string): Promise<Measurement> {
    const { data } = await apiClient.get<Measurement>(`/measurements/${measurementId}`)
    return data
  },

  async create(input: MeasurementCreateInput): Promise<Measurement> {
    const { data } = await apiClient.post<Measurement>("/measurements", input)
    return data
  },

  async update(measurementId: string, input: MeasurementUpdateInput): Promise<Measurement> {
    const { data } = await apiClient.patch<Measurement>(`/measurements/${measurementId}`, input)
    return data
  },

  /** TRAINER/SUPER_ADMIN only - CLIENT gets 403. Only includes clients who
   * have at least one prior measurement but are now overdue; clients never
   * measured at all are a separate "missing" bucket (see the Super Admin
   * dashboard), not included here. */
  async listPending(): Promise<PendingMeasurement[]> {
    const { data } = await apiClient.get<PendingMeasurement[]>("/measurements/pending")
    return data
  },
}
