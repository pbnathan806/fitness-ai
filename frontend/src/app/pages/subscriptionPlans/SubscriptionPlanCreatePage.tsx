import { useNavigate, Link } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  SubscriptionPlanForm,
  type SubscriptionPlanFormValues,
} from "@/app/pages/subscriptionPlans/components/SubscriptionPlanForm"
import { subscriptionPlanService } from "@/services/subscriptionPlanService"
import { getApiErrorMessage } from "@/lib/errors"

export function SubscriptionPlanCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (values: SubscriptionPlanFormValues) =>
      subscriptionPlanService.createPlan({
        name: values.name,
        description: values.description || null,
        duration_days: values.duration_days,
        price: values.price,
        currency: values.currency.toUpperCase(),
        sessions_per_week: values.sessions_per_week ?? null,
        max_sessions_per_month: values.max_sessions_per_month ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscription-plans", "all"] })
      toast.success("Subscription plan created successfully.")
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
          <CardTitle>New Subscription Plan</CardTitle>
          <CardDescription>Create a plan clients can subscribe to.</CardDescription>
        </CardHeader>
        <CardContent>
          <SubscriptionPlanForm
            mode="create"
            // Numeric fields start as empty strings so the inputs render blank;
            // zod's preprocess step (see SubscriptionPlanForm) coerces them
            // back to numbers on validation, so the `number` type here is
            // only accurate post-submit, not for this initial empty state.
            defaultValues={
              {
                name: "",
                description: "",
                duration_days: "",
                price: "",
                currency: "",
                sessions_per_week: undefined,
                max_sessions_per_month: undefined,
                is_active: true,
              } as unknown as SubscriptionPlanFormValues
            }
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Create Plan"
          />
        </CardContent>
      </Card>
    </div>
  )
}
