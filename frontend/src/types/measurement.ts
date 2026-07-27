export interface LatestMeasurement {
  weight_kg: number | null
  previous_weight_kg: number | null
  weight_change: number | null
  waist_cm: number | null
  previous_waist_cm: number | null
  waist_change: number | null
  recorded_at: string | null
}
