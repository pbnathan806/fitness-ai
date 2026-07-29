import { apiClient } from "@/services/apiClient"
import type { PaginatedResponse } from "@/types/dashboard"
import type {
  AffectedSession,
  ClientSubscription,
  PaginatedSubscriptions,
  Subscription,
  SubscriptionCreateInput,
  SubscriptionEligibility,
  SubscriptionExpireResult,
  SubscriptionUpdateInput,
} from "@/types/subscription"

// No "subscriptions for client X" endpoint exists for SUPER_ADMIN, so (as in
// dashboardService/assignmentService) a single generously-sized page of the
// platform-wide list is fetched and filtered client-side by client_id.
const LOOKUP_PAGE_SIZE = 100

// The Subscriptions module list page needs client-side status/payment-status
// filtering (as `GET /subscriptions` has no such query params), so - as in
// clientService.listAllClients - every page is walked once, bounded by
// LIST_ALL_MAX_PAGES, and filtered/paginated in the browser.
const LIST_ALL_PAGE_SIZE = 100
const LIST_ALL_MAX_PAGES = 50

export const subscriptionService = {
  async listSubscriptionsForLookup(): Promise<Subscription[]> {
    const { data } = await apiClient.get<PaginatedResponse<Subscription>>("/subscriptions", {
      params: { page: 1, page_size: LOOKUP_PAGE_SIZE },
    })
    return data.items
  },

  async listSubscriptions(page: number, pageSize: number): Promise<PaginatedSubscriptions> {
    const { data } = await apiClient.get<PaginatedSubscriptions>("/subscriptions", {
      params: { page, page_size: pageSize },
    })
    return data
  },

  /** Calls `subscriptionService.listSubscriptions` (not `this.listSubscriptions`)
   * since this is passed around as a bare function reference (e.g. react-query
   * `queryFn`), which would otherwise lose its `this` binding. */
  async listAllSubscriptions(): Promise<Subscription[]> {
    const first = await subscriptionService.listSubscriptions(1, LIST_ALL_PAGE_SIZE)
    const totalPages = Math.min(first.total_pages, LIST_ALL_MAX_PAGES)
    if (totalPages <= 1) return first.items

    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => subscriptionService.listSubscriptions(i + 2, LIST_ALL_PAGE_SIZE)),
    )
    return [first.items, ...rest.map((page) => page.items)].flat()
  },

  async getSubscription(subscriptionId: string): Promise<Subscription> {
    const { data } = await apiClient.get<Subscription>(`/subscriptions/${subscriptionId}`)
    return data
  },

  async createSubscription(payload: SubscriptionCreateInput): Promise<Subscription> {
    const { data } = await apiClient.post<Subscription>("/subscriptions", payload)
    return data
  },

  async updateSubscription(subscriptionId: string, payload: SubscriptionUpdateInput): Promise<Subscription> {
    const { data } = await apiClient.patch<Subscription>(`/subscriptions/${subscriptionId}`, payload)
    return data
  },

  async getMySubscriptions(): Promise<ClientSubscription[]> {
    const { data } = await apiClient.get<ClientSubscription[]>("/subscriptions/my-subscriptions")
    return data
  },

  async getClientEligibility(clientId: string): Promise<SubscriptionEligibility> {
    const { data } = await apiClient.get<SubscriptionEligibility>(`/subscriptions/client/${clientId}/eligibility`)
    return data
  },

  /** Preview of future SCHEDULED sessions that would be cancelled if this
   * subscription were expired now - fetched before showing the confirm
   * dialog, never as a side effect. */
  async getExpiryImpact(subscriptionId: string): Promise<AffectedSession[]> {
    const { data } = await apiClient.get<AffectedSession[]>(`/subscriptions/${subscriptionId}/expiry-impact`)
    return data
  },

  async expireSubscription(subscriptionId: string): Promise<SubscriptionExpireResult> {
    const { data } = await apiClient.post<SubscriptionExpireResult>(`/subscriptions/${subscriptionId}/expire`)
    return data
  },
}
