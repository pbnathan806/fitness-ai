import { apiClient } from "@/services/apiClient"
import type {
  PaginatedTrainers,
  Trainer,
  TrainerAvailability,
  TrainerAvailabilityInput,
  TrainerCreateInput,
  TrainerCreateResult,
  TrainerListParams,
  TrainerPerformance,
  TrainerSelfUpdateInput,
  TrainerSummary,
  TrainerUpdateInput,
} from "@/types/trainer"

export const trainerService = {
  async listTrainers(params: TrainerListParams): Promise<PaginatedTrainers> {
    const { data } = await apiClient.get<PaginatedTrainers>("/trainers", { params })
    return data
  },

  async getTrainer(trainerId: string): Promise<Trainer> {
    const { data } = await apiClient.get<Trainer>(`/trainers/${trainerId}`)
    return data
  },

  async createTrainer(payload: TrainerCreateInput): Promise<TrainerCreateResult> {
    const { data } = await apiClient.post<TrainerCreateResult>("/trainers", payload)
    return data
  },

  async updateTrainer(trainerId: string, payload: TrainerUpdateInput): Promise<Trainer> {
    const { data } = await apiClient.put<Trainer>(`/trainers/${trainerId}`, payload)
    return data
  },

  async updateTrainerStatus(trainerId: string, isActive: boolean): Promise<Trainer> {
    const { data } = await apiClient.patch<Trainer>(`/trainers/${trainerId}/status`, { is_active: isActive })
    return data
  },

  async getSummary(trainerId: string): Promise<TrainerSummary> {
    const { data } = await apiClient.get<TrainerSummary>(`/trainers/${trainerId}/summary`)
    return data
  },

  async getPerformance(trainerId: string): Promise<TrainerPerformance> {
    const { data } = await apiClient.get<TrainerPerformance>(`/trainers/${trainerId}/performance`)
    return data
  },

  async getSelf(): Promise<Trainer> {
    const { data } = await apiClient.get<Trainer>("/trainers/me")
    return data
  },

  async updateSelf(payload: TrainerSelfUpdateInput): Promise<Trainer> {
    const { data } = await apiClient.put<Trainer>("/trainers/me", payload)
    return data
  },

  async listMyAvailability(): Promise<TrainerAvailability[]> {
    const { data } = await apiClient.get<TrainerAvailability[]>("/trainers/me/availability")
    return data
  },

  async createAvailability(payload: TrainerAvailabilityInput): Promise<TrainerAvailability> {
    const { data } = await apiClient.post<TrainerAvailability>("/trainers/me/availability", payload)
    return data
  },

  async updateAvailability(
    availabilityId: string,
    payload: TrainerAvailabilityInput,
  ): Promise<TrainerAvailability> {
    const { data } = await apiClient.put<TrainerAvailability>(
      `/trainers/me/availability/${availabilityId}`,
      payload,
    )
    return data
  },

  async deleteAvailability(availabilityId: string): Promise<void> {
    await apiClient.delete(`/trainers/me/availability/${availabilityId}`)
  },
}
