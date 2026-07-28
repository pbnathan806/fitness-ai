import type { PaginatedResponse } from "@/types/dashboard"

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

export type PaginatedSubscriptions = PaginatedResponse<Subscription>

export interface SubscriptionCreateInput {
  client_id: string
  subscription_plan_id: string
  start_date?: string | null
  auto_renew: boolean
  notes?: string | null
}

/** Only status, payment_status, end_date, auto_renew, and notes are editable -
 * client_id, subscription_plan_id, and every plan-snapshot/start_date field
 * are immutable server-side (Task-16.3.1) and are never sent here. */
export interface SubscriptionUpdateInput {
  status?: SubscriptionStatus
  payment_status?: SubscriptionPaymentStatus
  end_date?: string
  auto_renew?: boolean
  notes?: string | null
}

/** Summary shape returned by `GET /subscriptions/my-subscriptions` - narrower
 * than `Subscription` (no ids, duration, or sessions-per-week). */
export interface ClientSubscription {
  id: string
  plan_name: string
  plan_price: number
  plan_currency: string
  payment_status: SubscriptionPaymentStatus
  status: SubscriptionStatus
  start_date: string
  end_date: string
}

/** Deliberately excludes plan_price, plan_currency, payment_status, notes,
 * auto_renew, and subscription ids - trainers must never receive financial or
 * historical subscription data (see backend SubscriptionEligibility). */
export interface SubscriptionEligibility {
  client_id: string
  plan_name: string
  status: SubscriptionStatus
  end_date: string
  can_schedule_sessions: boolean
}

export interface SubscriptionPlan {
  id: string
  name: string
  description: string | null
  duration_days: number
  price: number
  currency: string
  max_sessions_per_month: number | null
  sessions_per_week: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SubscriptionPlanCreateInput {
  name: string
  description?: string | null
  duration_days: number
  price: number
  currency: string
  max_sessions_per_month?: number | null
  sessions_per_week?: number | null
}

/** name, duration_days, and currency are immutable server-side
 * (Task-16.3.1) and are never sent here. */
export interface SubscriptionPlanUpdateInput {
  description?: string | null
  price?: number
  max_sessions_per_month?: number | null
  sessions_per_week?: number | null
  is_active?: boolean
}
