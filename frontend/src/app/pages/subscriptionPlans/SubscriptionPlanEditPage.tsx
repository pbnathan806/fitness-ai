import { useNavigate, useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import {
  SubscriptionPlanForm,
  type SubscriptionPlanFormValues,
} from "@/app/pages/subscriptionPlans/components/SubscriptionPlanForm"
import { subscriptionPlanService } from "@/services/subscriptionPlanService"
import { getApiErrorMessage } from "@/lib/errors"

/** Doubles as the plan "view" screen (Task 22.5's list actions include View
 * and Edit, but the module has no separate details route) - immutable fields
 * (name, duration_days, currency) are rendered disabled rather than omitted. */
export function SubscriptionPlanEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const planQuery = useQuery({
    queryKey: ["subscription-plans", id],
    queryFn: () => subscriptionPlanService.getPlan(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (values: SubscriptionPlanFormValues) =>
      subscriptionPlanService.updatePlan(id!, {
        description: values.description || null,
        price: values.price,
        sessions_per_week: values.sessions_per_week ?? null,
        max_sessions_per_month: values.max_sessions_per_month ?? null,
        is_active: values.is_active,
      }),
    onSuccess: (updatedPlan) => {
      queryClient.setQueryData(["subscription-plans", id], updatedPlan)
      queryClient.invalidateQueries({ queryKey: ["subscription-plans", "all"] })
      toast.success("Subscription plan updated successfully.")
      navigate("/super-admin/subscription-plans")
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/subscription-plans" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to subscription plans
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>{planQuery.data ? planQuery.data.name : "Subscription Plan"}</CardTitle>
          <CardDescription>View plan details and update its editable fields.</CardDescription>
        </CardHeader>
        <CardContent>
          {planQuery.isLoading && <LoadingSpinner label="Loading subscription plan..." className="py-8" />}

          {planQuery.isError && (
            <ErrorState message={getApiErrorMessage(planQuery.error)} onRetry={() => planQuery.refetch()} />
          )}

          {planQuery.data && (
            <SubscriptionPlanForm
              mode="edit"
              defaultValues={{
                name: planQuery.data.name,
                description: planQuery.data.description ?? "",
                duration_days: planQuery.data.duration_days,
                price: planQuery.data.price,
                currency: planQuery.data.currency,
                sessions_per_week: planQuery.data.sessions_per_week ?? undefined,
                max_sessions_per_month: planQuery.data.max_sessions_per_month ?? undefined,
                is_active: planQuery.data.is_active,
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
