import { apiClient } from "@/services/apiClient"
import type { PaginatedResponse } from "@/types/dashboard"
import type { Subscription } from "@/types/subscription"

// No "subscriptions for client X" endpoint exists for SUPER_ADMIN, so (as in
// dashboardService/assignmentService) a single generously-sized page of the
// platform-wide list is fetched and filtered client-side by client_id.
const LOOKUP_PAGE_SIZE = 100

export const subscriptionService = {
  async listSubscriptionsForLookup(): Promise<Subscription[]> {
    const { data } = await apiClient.get<PaginatedResponse<Subscription>>("/subscriptions", {
      params: { page: 1, page_size: LOOKUP_PAGE_SIZE },
    })
    return data.items
  },
}
