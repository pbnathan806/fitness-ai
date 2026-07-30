import type { PaginatedResponse } from "@/types/dashboard"

export interface Measurement {
  id: string
  client_id: string
  weight_kg: number | null
  body_fat_percentage: number | null
  chest_cm: number | null
  waist_cm: number | null
  hips_cm: number | null
  left_arm_cm: number | null
  right_arm_cm: number | null
  left_thigh_cm: number | null
  right_thigh_cm: number | null
  resting_heart_rate: number | null
  recorded_by: string
  recorded_at: string
  created_at: string
  updated_at: string
}

export interface MeasurementCreateInput {
  client_id: string
  recorded_at?: string | null
  weight_kg: number | null
  body_fat_percentage: number | null
  chest_cm: number | null
  waist_cm: number | null
  hips_cm: number | null
  left_arm_cm: number | null
  right_arm_cm: number | null
  left_thigh_cm: number | null
  right_thigh_cm: number | null
  resting_heart_rate: number | null
}

export interface MeasurementUpdateInput {
  weight_kg?: number | null
  body_fat_percentage?: number | null
  chest_cm?: number | null
  waist_cm?: number | null
  hips_cm?: number | null
  left_arm_cm?: number | null
  right_arm_cm?: number | null
  left_thigh_cm?: number | null
  right_thigh_cm?: number | null
  resting_heart_rate?: number | null
}

export interface LatestMeasurement {
  weight_kg: number | null
  previous_weight_kg: number | null
  weight_change: number | null
  body_fat_percentage: number | null
  previous_body_fat_percentage: number | null
  body_fat_change: number | null
  chest_cm: number | null
  previous_chest_cm: number | null
  chest_change: number | null
  waist_cm: number | null
  previous_waist_cm: number | null
  waist_change: number | null
  hips_cm: number | null
  previous_hips_cm: number | null
  hips_change: number | null
  left_arm_cm: number | null
  previous_left_arm_cm: number | null
  left_arm_change: number | null
  right_arm_cm: number | null
  previous_right_arm_cm: number | null
  right_arm_change: number | null
  left_thigh_cm: number | null
  previous_left_thigh_cm: number | null
  left_thigh_change: number | null
  right_thigh_cm: number | null
  previous_right_thigh_cm: number | null
  right_thigh_change: number | null
  resting_heart_rate: number | null
  previous_resting_heart_rate: number | null
  resting_heart_rate_change: number | null
  recorded_at: string | null
}

export type PaginatedMeasurements = PaginatedResponse<Measurement>

export interface PendingMeasurement {
  client_id: string
  client_name: string
  last_measurement_date: string
  days_overdue: number
}
