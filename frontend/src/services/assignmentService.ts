import { apiClient } from "@/services/apiClient"
import type { PaginatedResponse } from "@/types/dashboard"
import type { Assignment } from "@/types/assignment"

// There is no "assignments for client X" endpoint for SUPER_ADMIN and no
// trainer-directory endpoint at all (Task 22.3 scope). Same convention as
// dashboardService: a single generously-sized page of the platform-wide list
// is fetched and filtered client-side rather than walking every page.
const LOOKUP_PAGE_SIZE = 100

export const assignmentService = {
  async listAssignmentsForLookup(): Promise<Assignment[]> {
    const { data } = await apiClient.get<PaginatedResponse<Assignment>>("/assignments", {
      params: { page: 1, page_size: LOOKUP_PAGE_SIZE },
    })
    return data.items
  },
}
