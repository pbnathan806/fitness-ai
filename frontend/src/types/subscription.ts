export type SubscriptionStatus = "ACTIVE" | "EXPIRED" | "PAUSED" | "CANCELLED"
export type SubscriptionPaymentStatus = "PAID" | "PENDING" | "FAILED" | "REFUNDED"

export interface Subscription {
  id: string
  client_id: string
  subscription_plan_id: string
  plan_name: string
  plan_price: number
  plan_currency: string
  plan_duration_days: number
  plan_sessions_per_week: number | null
  start_date: string
  end_date: string
  status: SubscriptionStatus
  payment_status: SubscriptionPaymentStatus
  auto_renew: boolean
  notes: string | null
  created_at: string
  updated_at: string
}
