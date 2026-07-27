export interface CheckIn {
  id: string
  client_id: string
  sleep_hours: number | null
  water_intake_liters: number | null
  energy_level: number | null
  mood: number | null
  workout_completed: boolean | null
  diet_followed: boolean | null
  notes: string | null
  submitted_by: string
  submitted_at: string
  created_at: string
  updated_at: string
}
