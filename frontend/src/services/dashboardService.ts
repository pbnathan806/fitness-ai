import { apiClient } from "@/services/apiClient"
import type {
  DashboardCheckIn,
  DashboardClient,
  DashboardMeasurement,
  DashboardSession,
  PaginatedResponse,
  SuperAdminDashboardStats,
} from "@/types/dashboard"

// Widget lists have no dedicated backend endpoints (Task 21's dashboard API is
// stats-only) - a single generously-sized page of each existing paginated
// list is fetched and filtered/sorted client-side rather than walking pages.
const WIDGET_LIST_PAGE_SIZE = 100
const ACTIVITY_LIST_PAGE_SIZE = 5

export const dashboardService = {
  async getSuperAdminStats(): Promise<SuperAdminDashboardStats> {
    const { data } = await apiClient.get<SuperAdminDashboardStats>("/dashboard/super-admin")
    return data
  },

  async listSessionsForUpcomingWidget(): Promise<DashboardSession[]> {
    const { data } = await apiClient.get<PaginatedResponse<DashboardSession>>("/sessions", {
      params: { page: 1, page_size: WIDGET_LIST_PAGE_SIZE },
    })
    return data.items
  },

  async listRecentCheckIns(): Promise<DashboardCheckIn[]> {
    const { data } = await apiClient.get<PaginatedResponse<DashboardCheckIn>>("/check-ins", {
      params: { page: 1, page_size: ACTIVITY_LIST_PAGE_SIZE },
    })
    return data.items
  },

  async listRecentMeasurements(): Promise<DashboardMeasurement[]> {
    const { data } = await apiClient.get<PaginatedResponse<DashboardMeasurement>>("/measurements", {
      params: { page: 1, page_size: ACTIVITY_LIST_PAGE_SIZE },
    })
    return data.items
  },

  async listClientsForNameLookup(): Promise<DashboardClient[]> {
    const { data } = await apiClient.get<PaginatedResponse<DashboardClient>>("/clients", {
      params: { page: 1, page_size: WIDGET_LIST_PAGE_SIZE },
    })
    return data.items
  },
}
