import { apiClient } from "@/services/apiClient"
import type {
  SubscriptionPlan,
  SubscriptionPlanCreateInput,
  SubscriptionPlanUpdateInput,
} from "@/types/subscription"

export const subscriptionPlanService = {
  /** `GET /subscription-plans` only ever returns active plans - the backend
   * has no query param to include inactive ones (SubscriptionPlanService.list_active_plans). */
  async listPlans(): Promise<SubscriptionPlan[]> {
    const { data } = await apiClient.get<SubscriptionPlan[]>("/subscription-plans")
    return data
  },

  async getPlan(planId: string): Promise<SubscriptionPlan> {
    const { data } = await apiClient.get<SubscriptionPlan>(`/subscription-plans/${planId}`)
    return data
  },

  async createPlan(payload: SubscriptionPlanCreateInput): Promise<SubscriptionPlan> {
    const { data } = await apiClient.post<SubscriptionPlan>("/subscription-plans", payload)
    return data
  },

  async updatePlan(planId: string, payload: SubscriptionPlanUpdateInput): Promise<SubscriptionPlan> {
    const { data } = await apiClient.put<SubscriptionPlan>(`/subscription-plans/${planId}`, payload)
    return data
  },
}
