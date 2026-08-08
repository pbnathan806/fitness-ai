import type { PaginatedResponse } from "@/types/dashboard"

export interface PhysicalAssessment {
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
  // Groundwork only - always null until a photo upload capability is
  // built. Not present on the create/update input types below since
  // there's no upload mechanism yet to populate them.
  front_photo_url: string | null
  back_photo_url: string | null
  side_photo_url: string | null
  recorded_by: string
  recorded_at: string
  created_at: string
  updated_at: string
}

export interface PhysicalAssessmentCreateInput {
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

export interface PhysicalAssessmentUpdateInput {
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

export interface LatestPhysicalAssessment {
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

export type PaginatedPhysicalAssessments = PaginatedResponse<PhysicalAssessment>

export interface PendingPhysicalAssessment {
  client_id: string
  client_name: string
  last_physical_assessment_date: string
  days_overdue: number
}

export interface PendingPhysicalAssessmentsResponse {
  items: PendingPhysicalAssessment[]
  /** The application-configured overdue threshold this list was computed
   * against - exposed here since TRAINER has no other way to read it
   * (GET /application-settings is SUPER_ADMIN-only). */
  overdue_threshold_days: number
  /** Timezone this list's dates were bucketed in - the caller's own profile
   * timezone for a TRAINER, "Asia/Kolkata" for a SUPER_ADMIN. */
  timezone: string
}
