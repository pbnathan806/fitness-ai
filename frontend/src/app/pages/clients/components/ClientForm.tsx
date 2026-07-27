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
  password: z.string().min(8, "Password must be at least 8 characters"),
  ...baseFields,
})

const editSchema = z.object(baseFields)

export type ClientFormValues = z.infer<typeof createSchema>

interface ClientFormProps {
  mode: "create" | "edit"
  defaultValues?: Partial<ClientFormValues>
  onSubmit: (values: ClientFormValues) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Create/Edit Client form (Task 22.3). Reused by both routes - `mode` swaps
 * in the email/password fields (create-only, since PUT /clients/{id} cannot
 * change either) and the validation schema.
 *
 * Date of Birth, Gender, and Emergency Contact are intentionally omitted:
 * the backend's Client create/update API has no fields for them, and this
 * task must use the existing backend as-is without modification. See the
 * task's "Known limitations" note. */
export function ClientForm({
  mode,
  defaultValues,
  onSubmit,
  isSubmitting,
  submitErrorMessage,
  submitLabel,
}: ClientFormProps) {
  const schema = mode === "create" ? createSchema : editSchema
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClientFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<ClientFormValues>,
    defaultValues,
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {mode === "create" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              {...register("password")}
            />
            {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="first_name">First Name</Label>
          <Input id="first_name" aria-invalid={!!errors.first_name} {...register("first_name")} />
          {errors.first_name && <p className="text-sm text-destructive">{errors.first_name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="last_name">Last Name</Label>
          <Input id="last_name" aria-invalid={!!errors.last_name} {...register("last_name")} />
          {errors.last_name && <p className="text-sm text-destructive">{errors.last_name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="phone_number">Phone Number</Label>
          <Input
            id="phone_number"
            type="tel"
            autoComplete="tel"
            aria-invalid={!!errors.phone_number}
            {...register("phone_number")}
          />
          {errors.phone_number && <p className="text-sm text-destructive">{errors.phone_number.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="timezone">Timezone</Label>
          <Select id="timezone" aria-invalid={!!errors.timezone} defaultValue="" {...register("timezone")}>
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

      {submitErrorMessage && <ErrorState title="Couldn't save client" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
