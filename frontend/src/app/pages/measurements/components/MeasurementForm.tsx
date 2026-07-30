import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ErrorState } from "@/components/common/ErrorState"
import type { Measurement, MeasurementUpdateInput } from "@/types/measurement"

const optionalNumber = (min: number, max: number) =>
  z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : Number(value)),
    z.number().min(min).max(max).optional(),
  )

const optionalInt = (min: number, max: number) =>
  z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : Number(value)),
    z.number().int().min(min).max(max).optional(),
  )

const schema = z.object({
  weight_kg: optionalNumber(0, 500),
  body_fat_percentage: optionalNumber(0, 100),
  chest_cm: optionalNumber(0, 300),
  waist_cm: optionalNumber(0, 300),
  hips_cm: optionalNumber(0, 300),
  left_arm_cm: optionalNumber(0, 300),
  right_arm_cm: optionalNumber(0, 300),
  left_thigh_cm: optionalNumber(0, 300),
  right_thigh_cm: optionalNumber(0, 300),
  resting_heart_rate: optionalInt(20, 250),
})

// Same raw-string-in / resolved-number-out split as CheckInForm: native
// <input type="number"> always hands react-hook-form a string, and zod's
// preprocess only turns it into a number in the resolved output.
type MeasurementFormInput = z.input<typeof schema>
type MeasurementFormOutput = z.output<typeof schema>

function toInputValue(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value)
}

interface FieldSpec {
  name: keyof MeasurementFormOutput
  label: string
  step: string
  min: number
  max: number
}

const FIELDS: FieldSpec[] = [
  { name: "weight_kg", label: "Weight (kg)", step: "0.1", min: 0, max: 500 },
  { name: "body_fat_percentage", label: "Body Fat (%)", step: "0.1", min: 0, max: 100 },
  { name: "chest_cm", label: "Chest (cm)", step: "0.1", min: 0, max: 300 },
  { name: "waist_cm", label: "Waist (cm)", step: "0.1", min: 0, max: 300 },
  { name: "hips_cm", label: "Hips (cm)", step: "0.1", min: 0, max: 300 },
  { name: "left_arm_cm", label: "Left Arm (cm)", step: "0.1", min: 0, max: 300 },
  { name: "right_arm_cm", label: "Right Arm (cm)", step: "0.1", min: 0, max: 300 },
  { name: "left_thigh_cm", label: "Left Thigh (cm)", step: "0.1", min: 0, max: 300 },
  { name: "right_thigh_cm", label: "Right Thigh (cm)", step: "0.1", min: 0, max: 300 },
  { name: "resting_heart_rate", label: "Resting Heart Rate (bpm)", step: "1", min: 20, max: 250 },
]

interface MeasurementFormProps {
  /** Existing measurement to prefill from when editing; omit for a fresh submission. */
  measurement?: Measurement
  onSubmit: (values: MeasurementUpdateInput) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Shared create/edit form for the ten body-measurement fields - used for
 * both POST /measurements (Add) and PATCH /measurements/{id} (Edit). Every
 * field is optional, but the backend rejects a payload left with none of
 * them populated. */
export function MeasurementForm({
  measurement,
  onSubmit,
  isSubmitting,
  submitErrorMessage,
  submitLabel,
}: MeasurementFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<MeasurementFormInput, unknown, MeasurementFormOutput>({
    resolver: zodResolver(schema),
    values: {
      weight_kg: toInputValue(measurement?.weight_kg),
      body_fat_percentage: toInputValue(measurement?.body_fat_percentage),
      chest_cm: toInputValue(measurement?.chest_cm),
      waist_cm: toInputValue(measurement?.waist_cm),
      hips_cm: toInputValue(measurement?.hips_cm),
      left_arm_cm: toInputValue(measurement?.left_arm_cm),
      right_arm_cm: toInputValue(measurement?.right_arm_cm),
      left_thigh_cm: toInputValue(measurement?.left_thigh_cm),
      right_thigh_cm: toInputValue(measurement?.right_thigh_cm),
      resting_heart_rate: toInputValue(measurement?.resting_heart_rate),
    },
  })

  function handleFormSubmit(values: MeasurementFormOutput) {
    onSubmit({
      weight_kg: values.weight_kg ?? null,
      body_fat_percentage: values.body_fat_percentage ?? null,
      chest_cm: values.chest_cm ?? null,
      waist_cm: values.waist_cm ?? null,
      hips_cm: values.hips_cm ?? null,
      left_arm_cm: values.left_arm_cm ?? null,
      right_arm_cm: values.right_arm_cm ?? null,
      left_thigh_cm: values.left_thigh_cm ?? null,
      right_thigh_cm: values.right_thigh_cm ?? null,
      resting_heart_rate: values.resting_heart_rate ?? null,
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FIELDS.map((field) => (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name}>{field.label}</Label>
            <Input
              id={field.name}
              type="number"
              step={field.step}
              min={field.min}
              max={field.max}
              aria-invalid={!!errors[field.name]}
              {...register(field.name)}
            />
            {errors[field.name] && <p className="text-sm text-destructive">{errors[field.name]?.message}</p>}
          </div>
        ))}
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't save measurement" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
