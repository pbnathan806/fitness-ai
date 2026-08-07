import { isAxiosError } from "axios"
import { apiClient } from "@/services/apiClient"
import type {
  LatestPhysicalAssessment,
  PhysicalAssessment,
  PhysicalAssessmentCreateInput,
  PhysicalAssessmentUpdateInput,
  PaginatedPhysicalAssessments,
  PendingPhysicalAssessment,
} from "@/types/physicalAssessment"

// `GET /physical-assessments` has no filter params, so (as in sessionService and
// checkInService) every page is walked once, bounded by LIST_ALL_MAX_PAGES.
const LIST_ALL_PAGE_SIZE = 100
const LIST_ALL_MAX_PAGES = 50

export const physicalAssessmentService = {
  /** Server-paginated list across all clients (SUPER_ADMIN), assigned
   * clients (TRAINER), or own records (CLIENT) - see backend
   * PhysicalAssessmentService.list_physical_assessments. */
  async list(page: number, pageSize: number): Promise<PaginatedPhysicalAssessments> {
    const { data } = await apiClient.get<PaginatedPhysicalAssessments>("/physical-assessments", {
      params: { page, page_size: pageSize },
    })
    return data
  },

  /** Calls `physicalAssessmentService.list` (not `this.list`) since this is passed
   * around as a bare function reference (e.g. react-query `queryFn`), which
   * would otherwise lose its `this` binding. */
  async listAllPhysicalAssessments(): Promise<PhysicalAssessment[]> {
    const first = await physicalAssessmentService.list(1, LIST_ALL_PAGE_SIZE)
    const totalPages = Math.min(first.total_pages, LIST_ALL_MAX_PAGES)
    if (totalPages <= 1) return first.items

    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => physicalAssessmentService.list(i + 2, LIST_ALL_PAGE_SIZE)),
    )
    return [first.items, ...rest.map((page) => page.items)].flat()
  },

  /** Returns null when the client has no physical assessments yet (backend 404s in that case). */
  async getLatestPhysicalAssessment(clientId: string): Promise<LatestPhysicalAssessment | null> {
    try {
      const { data } = await apiClient.get<LatestPhysicalAssessment>(`/physical-assessments/client/${clientId}/latest`)
      return data
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  /** Full history for a client, newest first. */
  async getClientPhysicalAssessments(clientId: string): Promise<PhysicalAssessment[]> {
    const { data } = await apiClient.get<PhysicalAssessment[]>(`/physical-assessments/client/${clientId}`)
    return data
  },

  async getPhysicalAssessment(physicalAssessmentId: string): Promise<PhysicalAssessment> {
    const { data } = await apiClient.get<PhysicalAssessment>(`/physical-assessments/${physicalAssessmentId}`)
    return data
  },

  async create(input: PhysicalAssessmentCreateInput): Promise<PhysicalAssessment> {
    const { data } = await apiClient.post<PhysicalAssessment>("/physical-assessments", input)
    return data
  },

  async update(physicalAssessmentId: string, input: PhysicalAssessmentUpdateInput): Promise<PhysicalAssessment> {
    const { data } = await apiClient.patch<PhysicalAssessment>(`/physical-assessments/${physicalAssessmentId}`, input)
    return data
  },

  /** TRAINER/SUPER_ADMIN only - CLIENT gets 403. Only includes clients who
   * have at least one prior physical assessment but are now overdue;
   * clients never assessed at all are a separate "missing" bucket (see the
   * Super Admin dashboard), not included here. */
  async listPending(): Promise<PendingPhysicalAssessment[]> {
    const { data } = await apiClient.get<PendingPhysicalAssessment[]>("/physical-assessments/pending")
    return data
  },
}
