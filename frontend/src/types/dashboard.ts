export interface SuperAdminDashboardStats {
  total_clients: number
  active_clients: number
  expired_clients: number
  inactive_clients: number
  total_trainers: number
  sessions_today: number
  upcoming_sessions_next_7_days: number
  measurements_recorded_this_month: number
  check_ins_submitted_today: number
  clients_missing_check_ins_today: number
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type DashboardSessionStatus = "SCHEDULED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED"

export interface DashboardSession {
  id: string
  client_id: string
  trainer_id: string
  scheduled_start: string
  scheduled_end: string
  status: DashboardSessionStatus
  meeting_type: string
}

export interface DashboardCheckIn {
  id: string
  client_id: string
  submitted_at: string
}

export interface DashboardMeasurement {
  id: string
  client_id: string
  recorded_at: string
}

export interface DashboardClient {
  id: string
  first_name: string
  last_name: string
}

/** Client-side composite feed item for the Recent Activity widget - the
 * backend has no unified activity/audit-log API, so check-ins and
 * measurements (each already timestamped) are merged and sorted here. */
export interface ActivityItem {
  id: string
  kind: "check-in" | "measurement"
  clientName: string
  timestamp: string
}
