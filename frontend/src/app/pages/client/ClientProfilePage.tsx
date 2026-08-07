import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { UserCog, Star } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { clientService } from "@/services/clientService"
import { assignmentService } from "@/services/assignmentService"
import { getApiErrorMessage } from "@/lib/errors"
import { SUPPORTED_TIMEZONES } from "@/lib/constants"

const profileSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  phone_number: z.string().max(20, "Phone number is too long").optional().or(z.literal("")),
  timezone: z.string().min(1, "Timezone is required"),
})

type ProfileFormValues = z.infer<typeof profileSchema>

/** Client self-profile page (Tier 1+2). Clients may update their own name,
 * phone number, and timezone here (`PUT /clients/me`) - email is immutable
 * everywhere by design. The "My Trainers" section is read-only, sourced from
 * `GET /assignments/my-trainers` (no create/remove controls - that stays a
 * SUPER_ADMIN-only action). */
export function ClientProfilePage() {
  const queryClient = useQueryClient()

  const selfQuery = useQuery({
    queryKey: ["clients", "me"],
    queryFn: clientService.getMe,
  })

  const trainersQuery = useQuery({
    queryKey: ["assignments", "my-trainers"],
    queryFn: assignmentService.getMyTrainers,
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema) as unknown as Resolver<ProfileFormValues>,
    values: selfQuery.data
      ? {
          first_name: selfQuery.data.first_name,
          last_name: selfQuery.data.last_name,
          phone_number: selfQuery.data.phone_number ?? "",
          timezone: selfQuery.data.timezone,
        }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (values: ProfileFormValues) =>
      clientService.updateMe({
        first_name: values.first_name,
        last_name: values.last_name,
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["clients", "me"], updated)
      toast.success("Profile updated successfully.")
      reset({
        first_name: updated.first_name,
        last_name: updated.last_name,
        phone_number: updated.phone_number ?? "",
        timezone: updated.timezone,
      })
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

  const client = selfQuery.data
  const trainerCount = trainersQuery.data?.length ?? 0

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">My Profile</h1>
        <p className="text-sm text-muted-foreground">View your profile and update your contact details.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Email is fixed and cannot be changed.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => updateMutation.mutate(values))} noValidate className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="profile-first-name">First Name</Label>
                <Input
                  id="profile-first-name"
                  autoComplete="given-name"
                  aria-invalid={!!errors.first_name}
                  {...register("first_name")}
                />
                {errors.first_name && <p className="text-sm text-destructive">{errors.first_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-last-name">Last Name</Label>
                <Input
                  id="profile-last-name"
                  autoComplete="family-name"
                  aria-invalid={!!errors.last_name}
                  {...register("last_name")}
                />
                {errors.last_name && <p className="text-sm text-destructive">{errors.last_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-email">Email</Label>
                <Input id="profile-email" value={client.email} disabled readOnly />
              </div>
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

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCog className="size-4 text-muted-foreground" aria-hidden="true" />
            My Trainers
          </CardTitle>
          {!trainersQuery.isLoading && !trainersQuery.isError && (
            <CardDescription>{trainerCount} assigned</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {trainersQuery.isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          )}

          {!trainersQuery.isLoading && trainersQuery.isError && (
            <ErrorState message="Unable to load your trainers." onRetry={() => trainersQuery.refetch()} />
          )}

          {!trainersQuery.isLoading && !trainersQuery.isError && trainerCount === 0 && (
            <EmptyState icon={UserCog} message="No trainers assigned yet." />
          )}

          {!trainersQuery.isLoading && !trainersQuery.isError && trainerCount > 0 && (
            <ul className="divide-y">
              {trainersQuery.data!.map((trainer) => (
                <li key={trainer.assignment_id} className="space-y-1 py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-sm font-medium">
                      {`${trainer.first_name ?? ""} ${trainer.last_name ?? ""}`.trim() || "Trainer"}
                    </p>
                    {trainer.is_primary && (
                      <Badge variant="default">
                        <Star className="size-3" />
                        Primary
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {[trainer.specialization, trainer.experience_years != null ? `${trainer.experience_years} yrs experience` : null, trainer.country]
                      .filter(Boolean)
                      .join(" · ") || "No further details provided."}
                  </p>
                  {trainer.bio && <p className="text-xs text-muted-foreground">{trainer.bio}</p>}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
