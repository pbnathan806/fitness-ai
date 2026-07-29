import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ErrorState } from "@/components/common/ErrorState"
import type { CheckIn, CheckInUpdateInput } from "@/types/checkIn"

const optionalNumber = (min: number, max: number) =>
  z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : Number(value)),
    z.number().min(min).max(max).optional(),
  )

const optionalScale = (min: number, max: number) =>
  z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? undefined : Number(value)),
    z.number().int().min(min).max(max).optional(),
  )

const optionalBoolean = z.preprocess(
  (value) => (value === "" || value === null || value === undefined ? undefined : value === "true"),
  z.boolean().optional(),
)

const schema = z.object({
  sleep_hours: optionalNumber(0, 24),
  water_intake_liters: optionalNumber(0, 20),
  energy_level: optionalScale(1, 5),
  mood: optionalScale(1, 5),
  workout_completed: optionalBoolean,
  diet_followed: optionalBoolean,
  notes: z.string().optional().or(z.literal("")),
})

// The DOM always hands react-hook-form raw strings (native <select>/<input>
// values); zod's preprocess steps turn those into numbers/booleans only in
// the resolved output. Typing the form against the input shape (all `unknown`
// going in) and the output shape (numbers/booleans coming out of handleSubmit)
// keeps both ends honest instead of casting through `unknown as number`.
type CheckInFormInput = z.input<typeof schema>
type CheckInFormOutput = z.output<typeof schema>

function toSelectValue(value: boolean | number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value)
}

interface CheckInFormProps {
  /** Existing check-in to prefill from when editing; omit for a fresh submission. */
  checkIn?: CheckIn
  onSubmit: (values: CheckInUpdateInput) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Shared create/edit form for the seven check-in wellness fields - used for
 * both POST /check-ins (Submit) and PATCH /check-ins/{id} (Edit) across all
 * three roles' Session Details screens. Every field is optional, but the
 * backend rejects a payload left with none of them populated. */
export function CheckInForm({ checkIn, onSubmit, isSubmitting, submitErrorMessage, submitLabel }: CheckInFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CheckInFormInput, unknown, CheckInFormOutput>({
    resolver: zodResolver(schema),
    values: {
      sleep_hours: toSelectValue(checkIn?.sleep_hours ?? null),
      water_intake_liters: toSelectValue(checkIn?.water_intake_liters ?? null),
      energy_level: toSelectValue(checkIn?.energy_level ?? null),
      mood: toSelectValue(checkIn?.mood ?? null),
      workout_completed: toSelectValue(checkIn?.workout_completed ?? null),
      diet_followed: toSelectValue(checkIn?.diet_followed ?? null),
      notes: checkIn?.notes ?? "",
    },
  })

  function handleFormSubmit(values: CheckInFormOutput) {
    onSubmit({
      sleep_hours: values.sleep_hours ?? null,
      water_intake_liters: values.water_intake_liters ?? null,
      energy_level: values.energy_level ?? null,
      mood: values.mood ?? null,
      workout_completed: values.workout_completed ?? null,
      diet_followed: values.diet_followed ?? null,
      notes: values.notes || null,
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="sleep_hours">Sleep (hours)</Label>
          <Input
            id="sleep_hours"
            type="number"
            step="0.5"
            min="0"
            max="24"
            aria-invalid={!!errors.sleep_hours}
            {...register("sleep_hours")}
          />
          {errors.sleep_hours && <p className="text-sm text-destructive">{errors.sleep_hours.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="water_intake_liters">Water Intake (liters)</Label>
          <Input
            id="water_intake_liters"
            type="number"
            step="0.1"
            min="0"
            max="20"
            aria-invalid={!!errors.water_intake_liters}
            {...register("water_intake_liters")}
          />
          {errors.water_intake_liters && (
            <p className="text-sm text-destructive">{errors.water_intake_liters.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="energy_level">Energy Level (1-5)</Label>
          <Select id="energy_level" aria-invalid={!!errors.energy_level} {...register("energy_level")}>
            <option value="">Not recorded</option>
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="mood">Mood (1-5)</Label>
          <Select id="mood" aria-invalid={!!errors.mood} {...register("mood")}>
            <option value="">Not recorded</option>
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="workout_completed">Workout Completed</Label>
          <Select id="workout_completed" {...register("workout_completed")}>
            <option value="">Not recorded</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="diet_followed">Diet Followed</Label>
          <Select id="diet_followed" {...register("diet_followed")}>
            <option value="">Not recorded</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea id="notes" aria-invalid={!!errors.notes} {...register("notes")} />
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't save check-in" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
