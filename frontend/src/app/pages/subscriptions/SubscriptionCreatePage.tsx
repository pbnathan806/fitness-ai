import { useNavigate, Link } from "react-router-dom"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ErrorState } from "@/components/common/ErrorState"
import { clientService } from "@/services/clientService"
import { subscriptionPlanService } from "@/services/subscriptionPlanService"
import { subscriptionService } from "@/services/subscriptionService"
import { getApiErrorMessage } from "@/lib/errors"

const schema = z.object({
  client_id: z.string().min(1, "Client is required"),
  subscription_plan_id: z.string().min(1, "Subscription plan is required"),
  start_date: z.string().optional().or(z.literal("")),
  auto_renew: z.boolean(),
  notes: z.string().max(1000, "Notes are too long").optional().or(z.literal("")),
})

type SubscriptionCreateFormValues = z.infer<typeof schema>

export function SubscriptionCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })
  const plansQuery = useQuery({ queryKey: ["subscription-plans", "all"], queryFn: subscriptionPlanService.listPlans })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SubscriptionCreateFormValues>({
    resolver: zodResolver(schema) as unknown as Resolver<SubscriptionCreateFormValues>,
    defaultValues: { client_id: "", subscription_plan_id: "", start_date: "", auto_renew: false, notes: "" },
  })

  const createMutation = useMutation({
    mutationFn: (values: SubscriptionCreateFormValues) =>
      subscriptionService.createSubscription({
        client_id: values.client_id,
        subscription_plan_id: values.subscription_plan_id,
        start_date: values.start_date || null,
        auto_renew: values.auto_renew,
        notes: values.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] })
      toast.success("Subscription created successfully.")
      navigate("/super-admin/subscriptions")
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/subscriptions" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to subscriptions
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>New Subscription</CardTitle>
          <CardDescription>Subscribe a client to a plan.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => createMutation.mutate(values))} noValidate className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="client_id">Client</Label>
                <Select
                  id="client_id"
                  aria-invalid={!!errors.client_id}
                  disabled={clientsQuery.isLoading}
                  defaultValue=""
                  {...register("client_id")}
                >
                  <option value="" disabled>
                    Select a client
                  </option>
                  {(clientsQuery.data ?? []).map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.first_name} {client.last_name} ({client.email})
                    </option>
                  ))}
                </Select>
                {errors.client_id && <p className="text-sm text-destructive">{errors.client_id.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="subscription_plan_id">Subscription Plan</Label>
                <Select
                  id="subscription_plan_id"
                  aria-invalid={!!errors.subscription_plan_id}
                  disabled={plansQuery.isLoading}
                  defaultValue=""
                  {...register("subscription_plan_id")}
                >
                  <option value="" disabled>
                    Select a plan
                  </option>
                  {(plansQuery.data ?? []).map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} ({plan.currency} {plan.price.toFixed(2)})
                    </option>
                  ))}
                </Select>
                {errors.subscription_plan_id && (
                  <p className="text-sm text-destructive">{errors.subscription_plan_id.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input id="start_date" type="date" aria-invalid={!!errors.start_date} {...register("start_date")} />
                <p className="text-xs text-muted-foreground">Defaults to today (India time) if left blank.</p>
                {errors.start_date && <p className="text-sm text-destructive">{errors.start_date.message}</p>}
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  id="auto_renew"
                  type="checkbox"
                  className="size-4 rounded border-input accent-primary"
                  {...register("auto_renew")}
                />
                <Label htmlFor="auto_renew" className="cursor-pointer">
                  Auto Renew
                </Label>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" aria-invalid={!!errors.notes} {...register("notes")} />
              {errors.notes && <p className="text-sm text-destructive">{errors.notes.message}</p>}
            </div>

            {createMutation.isError && (
              <ErrorState title="Couldn't create subscription" message={getApiErrorMessage(createMutation.error)} />
            )}

            <Button type="submit" disabled={createMutation.isPending} className="w-full sm:w-auto">
              {createMutation.isPending ? "Saving..." : "Create Subscription"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
