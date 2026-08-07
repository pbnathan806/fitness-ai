import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Camera } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ErrorState } from "@/components/common/ErrorState"
import type { PhysicalAssessment, PhysicalAssessmentUpdateInput } from "@/types/physicalAssessment"

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
type PhysicalAssessmentFormInput = z.input<typeof schema>
type PhysicalAssessmentFormOutput = z.output<typeof schema>

function toInputValue(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value)
}

interface FieldSpec {
  name: keyof PhysicalAssessmentFormOutput
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

// Groundwork only - see models/physical_assessment.py on the backend. These
// slots are visible but inert: no upload mechanism exists yet, so they're
// deliberately kept out of the zod schema and out of handleFormSubmit's
// payload. Not rendered for CLIENT at all - this form is never mounted on
// the client-facing (read-only) Physical Assessments page.
const PHOTO_SLOTS = [
  { key: "front", label: "Front Photo" },
  { key: "back", label: "Back Photo" },
  { key: "side", label: "Side Photo" },
] as const

interface PhysicalAssessmentFormProps {
  /** Existing physical assessment to prefill from when editing; omit for a fresh submission. */
  physicalAssessment?: PhysicalAssessment
  onSubmit: (values: PhysicalAssessmentUpdateInput) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Shared create/edit form for the ten body-measurement fields - used for
 * both POST /physical-assessments (Add) and PATCH /physical-assessments/{id}
 * (Edit). Every field is optional, but the backend rejects a payload left
 * with none of them populated. */
export function PhysicalAssessmentForm({
  physicalAssessment,
  onSubmit,
  isSubmitting,
  submitErrorMessage,
  submitLabel,
}: PhysicalAssessmentFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PhysicalAssessmentFormInput, unknown, PhysicalAssessmentFormOutput>({
    resolver: zodResolver(schema),
    values: {
      weight_kg: toInputValue(physicalAssessment?.weight_kg),
      body_fat_percentage: toInputValue(physicalAssessment?.body_fat_percentage),
      chest_cm: toInputValue(physicalAssessment?.chest_cm),
      waist_cm: toInputValue(physicalAssessment?.waist_cm),
      hips_cm: toInputValue(physicalAssessment?.hips_cm),
      left_arm_cm: toInputValue(physicalAssessment?.left_arm_cm),
      right_arm_cm: toInputValue(physicalAssessment?.right_arm_cm),
      left_thigh_cm: toInputValue(physicalAssessment?.left_thigh_cm),
      right_thigh_cm: toInputValue(physicalAssessment?.right_thigh_cm),
      resting_heart_rate: toInputValue(physicalAssessment?.resting_heart_rate),
    },
  })

  function handleFormSubmit(values: PhysicalAssessmentFormOutput) {
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

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label className="text-sm font-medium text-foreground">Photos</Label>
          <Badge variant="secondary">Coming soon</Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          Optional front, back, and side progress photos. Uploading isn't available yet.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {PHOTO_SLOTS.map((slot) => (
            <div key={slot.key} className="space-y-2">
              <Label htmlFor={`photo-${slot.key}`} className="text-muted-foreground">
                <Camera className="size-3.5" aria-hidden="true" />
                {slot.label}
              </Label>
              <Input id={`photo-${slot.key}`} type="file" accept="image/*" disabled />
            </div>
          ))}
        </div>
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't save physical assessment" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
