import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import { SUPPORTED_TIMEZONES } from "@/lib/constants"

const profileSchema = z.object({
  phone_number: z.string().max(20, "Phone number is too long").optional().or(z.literal("")),
  timezone: z.string().min(1, "Timezone is required"),
})

type ProfileFormValues = z.infer<typeof profileSchema>

/** Trainer self-profile page (Task 22.4.1). Trainers may only update their
 * own phone number and timezone here (`PUT /trainers/me`) - name, email, and
 * status are managed by SUPER_ADMIN via the Trainers module. */
export function TrainerProfilePage() {
  const queryClient = useQueryClient()

  const selfQuery = useQuery({
    queryKey: ["trainers", "me"],
    queryFn: trainerService.getSelf,
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema) as unknown as Resolver<ProfileFormValues>,
    values: selfQuery.data
      ? { phone_number: selfQuery.data.phone_number ?? "", timezone: selfQuery.data.timezone ?? "" }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (values: ProfileFormValues) =>
      trainerService.updateSelf({
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["trainers", "me"], updated)
      toast.success("Profile updated successfully.")
      reset({ phone_number: updated.phone_number ?? "", timezone: updated.timezone ?? "" })
    },
  })

  if (selfQuery.isLoading) {
    return <LoadingSpinner label="Loading your profile..." className="py-16" />
  }

  if (selfQuery.isError || !selfQuery.data) {
    return (
      <ErrorState
        title="Unable to load your profile"
        message={getApiErrorMessage(selfQuery.error)}
        onRetry={() => selfQuery.refetch()}
      />
    )
  }

  const trainer = selfQuery.data

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">My Profile</h1>
        <p className="text-sm text-muted-foreground">View your profile and update your contact details.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Name, email, and status are managed by your administrator.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-muted-foreground">Name</p>
            <p className="text-sm font-medium">
              {trainer.first_name} {trainer.last_name}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Email</p>
            <p className="text-sm font-medium">{trainer.email}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Status</p>
            <Badge variant={trainer.is_active ? "success" : "secondary"} className="mt-0.5">
              {trainer.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Contact Details</CardTitle>
          <CardDescription>Update your phone number and timezone.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => updateMutation.mutate(values))} noValidate className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="profile-phone">Phone Number</Label>
                <Input
                  id="profile-phone"
                  type="tel"
                  autoComplete="tel"
                  aria-invalid={!!errors.phone_number}
                  {...register("phone_number")}
                />
                {errors.phone_number && <p className="text-sm text-destructive">{errors.phone_number.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-timezone">Timezone</Label>
                <Select id="profile-timezone" aria-invalid={!!errors.timezone} {...register("timezone")}>
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

            {updateMutation.isError && (
              <ErrorState title="Couldn't save profile" message={getApiErrorMessage(updateMutation.error)} />
            )}

            <Button type="submit" disabled={updateMutation.isPending} className="w-full sm:w-auto">
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
