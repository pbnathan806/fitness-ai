export interface Trainer {
  id: string
  first_name: string | null
  last_name: string | null
  email: string
  phone_number: string | null
  timezone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PaginatedTrainers {
  items: Trainer[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface TrainerCreateInput {
  first_name: string
  last_name: string
  email: string
  phone_number?: string | null
  timezone: string
}

export interface TrainerCreateResult {
  id: string
  temporary_password: string
}

export interface TrainerUpdateInput {
  first_name?: string
  last_name?: string
  phone_number?: string | null
  timezone?: string
}

export interface TrainerSelfUpdateInput {
  phone_number?: string | null
  timezone?: string
}

export interface TrainerSummary {
  assigned_clients: number
  sessions_this_week: number
  completed_sessions_this_month: number
  pending_check_ins: number
  pending_measurements: number
}

export interface TrainerPerformance {
  assigned_clients: number
  completed_sessions: number
  completion_rate: number
  average_check_in_rate: number
}

/** `weekday` follows Python's `date.weekday()` convention used by the
 * backend: 0=Monday .. 6=Sunday. */
export interface TrainerAvailability {
  id: string
  trainer_id: string
  weekday: number
  start_time: string
  end_time: string
  is_available: boolean
  created_at: string
}

export interface TrainerAvailabilityInput {
  weekday: number
  start_time: string
  end_time: string
  is_available: boolean
}

export type TrainerListSortBy = "created_at" | "first_name"
export type SortDirection = "asc" | "desc"

export interface TrainerListParams {
  page: number
  page_size: number
  first_name?: string
  last_name?: string
  email?: string
  is_active?: boolean
  sort_by: TrainerListSortBy
  sort_dir: SortDirection
}
