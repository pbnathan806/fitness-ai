import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ErrorState } from "@/components/common/ErrorState"
import { SUPPORTED_TIMEZONES } from "@/lib/constants"

const baseFields = {
  first_name: z.string().min(1, "First name is required").max(100, "First name is too long"),
  last_name: z.string().min(1, "Last name is required").max(100, "Last name is too long"),
  phone_number: z
    .string()
    .max(20, "Phone number is too long")
    .optional()
    .or(z.literal("")),
  timezone: z.string().min(1, "Timezone is required"),
}

const createSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  ...baseFields,
})

const editSchema = z.object(baseFields)

export type TrainerFormValues = z.infer<typeof createSchema>

interface TrainerFormProps {
  mode: "create" | "edit"
  defaultValues?: Partial<TrainerFormValues>
  onSubmit: (values: TrainerFormValues) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Create/Edit Trainer form (Task 22.4.1). Reused by both routes - `mode`
 * swaps in the email field (create-only, since `PUT /trainers/{id}` cannot
 * change it) and the validation schema. Status is not a form field: it is
 * only editable via the dedicated Activate/Deactivate action. */
export function TrainerForm({
  mode,
  defaultValues,
  onSubmit,
  isSubmitting,
  submitErrorMessage,
  submitLabel,
}: TrainerFormProps) {
  const schema = mode === "create" ? createSchema : editSchema
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TrainerFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<TrainerFormValues>,
    defaultValues,
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="trainer-first-name">First Name</Label>
          <Input id="trainer-first-name" aria-invalid={!!errors.first_name} {...register("first_name")} />
          {errors.first_name && <p className="text-sm text-destructive">{errors.first_name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="trainer-last-name">Last Name</Label>
          <Input id="trainer-last-name" aria-invalid={!!errors.last_name} {...register("last_name")} />
          {errors.last_name && <p className="text-sm text-destructive">{errors.last_name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {mode === "create" && (
          <div className="space-y-2">
            <Label htmlFor="trainer-email">Email</Label>
            <Input
              id="trainer-email"
              type="email"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="trainer-phone">Phone Number</Label>
          <Input
            id="trainer-phone"
            type="tel"
            autoComplete="tel"
            aria-invalid={!!errors.phone_number}
            {...register("phone_number")}
          />
          {errors.phone_number && <p className="text-sm text-destructive">{errors.phone_number.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="trainer-timezone">Timezone</Label>
          <Select id="trainer-timezone" aria-invalid={!!errors.timezone} defaultValue="" {...register("timezone")}>
            <option value="" disabled>
              Select a timezone
            </option>
            {SUPPORTED_TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </Select>
          {errors.timezone && <p className="text-sm text-destructive">{errors.timezone.message}</p>}
        </div>
      </div>

      {submitErrorMessage && <ErrorState title="Couldn't save trainer" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
