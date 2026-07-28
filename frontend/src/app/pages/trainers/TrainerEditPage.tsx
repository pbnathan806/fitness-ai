import { useNavigate, useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { TrainerForm, type TrainerFormValues } from "@/app/pages/trainers/components/TrainerForm"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"

/** Edit Trainer page (Task 22.4.1). Reached only under `/super-admin/*`
 * (see routes.tsx), so the caller is always SUPER_ADMIN and gets the full
 * `PUT /trainers/{id}` edit - the TRAINER-restricted "phone/timezone only"
 * update flow lives on the separate self-profile page (`/trainer/profile`),
 * which calls `PUT /trainers/me` instead. */
export function TrainerEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const trainerQuery = useQuery({
    queryKey: ["trainers", id],
    queryFn: () => trainerService.getTrainer(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (values: TrainerFormValues) =>
      trainerService.updateTrainer(id!, {
        first_name: values.first_name,
        last_name: values.last_name,
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: (updatedTrainer) => {
      queryClient.setQueryData(["trainers", id], updatedTrainer)
      queryClient.invalidateQueries({ queryKey: ["trainers", "list"] })
      toast.success("Trainer updated successfully.")
      navigate(`/super-admin/trainers/${id}`)
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to={`/super-admin/trainers/${id}`} />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to trainer
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Edit Trainer</CardTitle>
          <CardDescription>
            {trainerQuery.data
              ? `${trainerQuery.data.first_name} ${trainerQuery.data.last_name}`
              : "Update trainer details."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {trainerQuery.isLoading && <LoadingSpinner label="Loading trainer details..." className="py-8" />}

          {trainerQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(trainerQuery.error, "This trainer could not be found.")}
              onRetry={() => trainerQuery.refetch()}
            />
          )}

          {trainerQuery.data && (
            <TrainerForm
              mode="edit"
              defaultValues={{
                first_name: trainerQuery.data.first_name ?? "",
                last_name: trainerQuery.data.last_name ?? "",
                phone_number: trainerQuery.data.phone_number ?? "",
                timezone: trainerQuery.data.timezone ?? "",
              }}
              onSubmit={(values) => updateMutation.mutate(values)}
              isSubmitting={updateMutation.isPending}
              submitErrorMessage={updateMutation.isError ? getApiErrorMessage(updateMutation.error) : null}
              submitLabel="Save Changes"
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
