import { useMemo } from "react"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ErrorState } from "@/components/common/ErrorState"
import { applicationSettingService } from "@/services/applicationSettingService"

// Configurable via the Application Settings screen (SUPER_ADMIN ->
// Settings), not hardcoded - see the `subscription_plan_currencies` seed
// migration for the default value.
const CURRENCY_SETTING_KEY = "subscription_plan_currencies"

function parseCurrencyOptions(value: string | undefined): string[] {
  if (!value) return []
  return Array.from(
    new Set(
      value
        .split(",")
        .map((code) => code.trim().toUpperCase())
        .filter(Boolean),
    ),
  )
}

/** Coerces the string values react-hook-form reads off text/number inputs
 * into numbers, treating a blank string as "not provided" so optional
 * numeric fields can be left empty instead of failing validation as NaN. */
function toNumber(val: unknown) {
  if (typeof val !== "string") return val
  const trimmed = val.trim()
  return trimmed === "" ? undefined : Number(trimmed)
}

const requiredPositiveInt = (message: string) =>
  z.preprocess(toNumber, z.number({ error: message }).int(message).positive(message))

const requiredPositiveNumber = (message: string) =>
  z.preprocess(toNumber, z.number({ error: message }).positive(message))

const optionalPositiveInt = z.preprocess(
  toNumber,
  z.number().int("Must be a whole number").positive("Must be greater than 0").optional(),
)

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name is too long"),
  description: z.string().max(1000, "Description is too long").optional().or(z.literal("")),
  duration_days: requiredPositiveInt("Duration is required"),
  price: requiredPositiveNumber("Price is required"),
  currency: z.string().min(1, "Currency is required"),
  sessions_per_week: optionalPositiveInt,
  max_sessions_per_month: optionalPositiveInt,
  is_active: z.boolean(),
})

export type SubscriptionPlanFormValues = z.infer<typeof schema>

interface SubscriptionPlanFormProps {
  mode: "create" | "edit"
  defaultValues: SubscriptionPlanFormValues
  onSubmit: (values: SubscriptionPlanFormValues) => void
  isSubmitting: boolean
  submitErrorMessage?: string | null
  submitLabel: string
}

/** Create/Edit Subscription Plan form (Task 22.5). `name`, `duration_days`,
 * and `currency` are immutable once a plan exists - in edit mode they're
 * shown (not hidden) but disabled, per the backend's ImmutableFieldError. */
export function SubscriptionPlanForm({
  mode,
  defaultValues,
  onSubmit,
  isSubmitting,
  submitErrorMessage,
  submitLabel,
}: SubscriptionPlanFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SubscriptionPlanFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SubscriptionPlanFormValues>,
    defaultValues,
  })

  const immutableDisabled = mode === "edit"

  const currencySettingQuery = useQuery({
    queryKey: ["application-settings", CURRENCY_SETTING_KEY],
    queryFn: () => applicationSettingService.getSetting(CURRENCY_SETTING_KEY),
  })

  // In edit mode a plan created before its currency was removed from the
  // setting (or before this setting existed at all) must still show its own
  // currency as a selectable option, or the disabled select would render blank.
  const currencyOptions = useMemo(() => {
    const configured = parseCurrencyOptions(currencySettingQuery.data?.value)
    if (defaultValues.currency && !configured.includes(defaultValues.currency.toUpperCase())) {
      return [defaultValues.currency.toUpperCase(), ...configured]
    }
    return configured
  }, [currencySettingQuery.data, defaultValues.currency])

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          aria-invalid={!!errors.name}
          disabled={immutableDisabled}
          {...register("name")}
        />
        {immutableDisabled && <p className="text-xs text-muted-foreground">Name cannot be changed after creation.</p>}
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea id="description" aria-invalid={!!errors.description} {...register("description")} />
        {errors.description && <p className="text-sm text-destructive">{errors.description.message}</p>}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="duration_days">Duration (Days)</Label>
          <Input
            id="duration_days"
            type="number"
            min={1}
            step={1}
            aria-invalid={!!errors.duration_days}
            disabled={immutableDisabled}
            {...register("duration_days")}
          />
          {errors.duration_days && <p className="text-sm text-destructive">{errors.duration_days.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="price">Price</Label>
          <Input
            id="price"
            type="number"
            min={0}
            step="0.01"
            aria-invalid={!!errors.price}
            {...register("price")}
          />
          {errors.price && <p className="text-sm text-destructive">{errors.price.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="currency">Currency</Label>
          <Select
            id="currency"
            aria-invalid={!!errors.currency}
            disabled={immutableDisabled || currencySettingQuery.isLoading}
            defaultValue={defaultValues.currency ? defaultValues.currency.toUpperCase() : ""}
            {...register("currency")}
          >
            {!defaultValues.currency && (
              <option value="" disabled>
                {currencySettingQuery.isLoading ? "Loading currencies..." : "Select a currency"}
              </option>
            )}
            {currencyOptions.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </Select>
          {immutableDisabled ? (
            <p className="text-xs text-muted-foreground">Currency cannot be changed after creation.</p>
          ) : (
            currencySettingQuery.isError && (
              <p className="text-xs text-destructive">
                Unable to load configured currencies. Manage the list under Settings.
              </p>
            )
          )}
          {errors.currency && <p className="text-sm text-destructive">{errors.currency.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="sessions_per_week">Sessions Per Week</Label>
          <Input
            id="sessions_per_week"
            type="number"
            min={1}
            step={1}
            aria-invalid={!!errors.sessions_per_week}
            {...register("sessions_per_week")}
          />
          {errors.sessions_per_week && <p className="text-sm text-destructive">{errors.sessions_per_week.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="max_sessions_per_month">Max Sessions Per Month</Label>
          <Input
            id="max_sessions_per_month"
            type="number"
            min={1}
            step={1}
            aria-invalid={!!errors.max_sessions_per_month}
            {...register("max_sessions_per_month")}
          />
          {errors.max_sessions_per_month && (
            <p className="text-sm text-destructive">{errors.max_sessions_per_month.message}</p>
          )}
        </div>
      </div>

      {mode === "edit" && (
        <div className="flex items-center gap-2">
          <input
            id="is_active"
            type="checkbox"
            className="size-4 rounded border-input accent-primary"
            {...register("is_active")}
          />
          <Label htmlFor="is_active" className="cursor-pointer">
            Active
          </Label>
        </div>
      )}

      {submitErrorMessage && <ErrorState title="Couldn't save subscription plan" message={submitErrorMessage} />}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  )
}
