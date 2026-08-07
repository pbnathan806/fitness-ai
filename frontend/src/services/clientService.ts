import { apiClient } from "@/services/apiClient"
import type { Client, ClientCreateInput, ClientUpdateInput, PaginatedClients } from "@/types/client"

const LIST_ALL_PAGE_SIZE = 100
// Safety cap so a runaway client count can't turn "load the list" into an
// unbounded number of requests; 50 pages at 100/page covers 5,000 clients.
const LIST_ALL_MAX_PAGES = 50

export const clientService = {
  async listClients(page: number, pageSize: number): Promise<PaginatedClients> {
    const { data } = await apiClient.get<PaginatedClients>("/clients", {
      params: { page, page_size: pageSize },
    })
    return data
  },

  /** The backend has no search/filter query params on `GET /clients`, so the
   * Clients list page walks every page once (bounded by LIST_ALL_MAX_PAGES)
   * and does search/filter/pagination client-side.
   *
   * Calls `clientService.listClients` (not `this.listClients`) since this is
   * passed around as a bare function reference (e.g. react-query `queryFn`),
   * which would otherwise lose its `this` binding. */
  async listAllClients(): Promise<Client[]> {
    const first = await clientService.listClients(1, LIST_ALL_PAGE_SIZE)
    const totalPages = Math.min(first.total_pages, LIST_ALL_MAX_PAGES)
    if (totalPages <= 1) return first.items

    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => clientService.listClients(i + 2, LIST_ALL_PAGE_SIZE)),
    )
    return [first.items, ...rest.map((page) => page.items)].flat()
  },

  async getClient(clientId: string): Promise<Client> {
    const { data } = await apiClient.get<Client>(`/clients/${clientId}`)
    return data
  },

  /** Resolves the current user's own client profile - used by CLIENT-facing
   * "My ..." pages that need their own client id (e.g. Physical
   * Assessments), where no client-id-scoped "my-X" endpoint exists on that
   * resource itself. */
  async getMe(): Promise<Client> {
    const { data } = await apiClient.get<Client>("/clients/me")
    return data
  },

  async updateMe(payload: ClientUpdateInput): Promise<Client> {
    const { data } = await apiClient.put<Client>("/clients/me", payload)
    return data
  },

  async createClient(payload: ClientCreateInput): Promise<Client> {
    const { data } = await apiClient.post<Client>("/clients", payload)
    return data
  },

  async updateClient(clientId: string, payload: ClientUpdateInput): Promise<Client> {
    const { data } = await apiClient.put<Client>(`/clients/${clientId}`, payload)
    return data
  },
}
