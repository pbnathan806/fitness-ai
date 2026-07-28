import { useParams, Link } from "react-router-dom"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { clientService } from "@/services/clientService"
import { subscriptionService } from "@/services/subscriptionService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { SUBSCRIPTION_STATUS_BADGE_VARIANT, SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import {
  SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT,
  SUBSCRIPTION_PAYMENT_STATUS_LABELS,
} from "@/lib/subscriptionPaymentStatus"
import type { SubscriptionPaymentStatus, SubscriptionStatus } from "@/types/subscription"

const STATUS_OPTIONS: SubscriptionStatus[] = ["ACTIVE", "EXPIRED", "PAUSED", "CANCELLED"]
const PAYMENT_STATUS_OPTIONS: SubscriptionPaymentStatus[] = ["PAID", "PENDING", "FAILED", "REFUNDED"]

const updateSchema = z.object({
  status: z.enum(["ACTIVE", "EXPIRED", "PAUSED", "CANCELLED"]),
  payment_status: z.enum(["PAID", "PENDING", "FAILED", "REFUNDED"]),
  end_date: z.string().min(1, "End date is required"),
  auto_renew: z.boolean(),
  notes: z.string().max(1000, "Notes are too long").optional().or(z.literal("")),
})

type SubscriptionUpdateFormValues = z.infer<typeof updateSchema>

export function SubscriptionDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const subscriptionQuery = useQuery({
    queryKey: ["subscriptions", id],
    queryFn: () => subscriptionService.getSubscription(id!),
    enabled: !!id,
  })

  const clientQuery = useQuery({
    queryKey: ["clients", subscriptionQuery.data?.client_id],
    queryFn: () => clientService.getClient(subscriptionQuery.data!.client_id),
    enabled: !!subscriptionQuery.data?.client_id,
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<SubscriptionUpdateFormValues>({
    resolver: zodResolver(updateSchema) as unknown as Resolver<SubscriptionUpdateFormValues>,
    values: subscriptionQuery.data
      ? {
          status: subscriptionQuery.data.status,
          payment_status: subscriptionQuery.data.payment_status,
          end_date: subscriptionQuery.data.end_date,
          auto_renew: subscriptionQuery.data.auto_renew,
          notes: subscriptionQuery.data.notes ?? "",
        }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (values: SubscriptionUpdateFormValues) =>
      subscriptionService.updateSubscription(id!, {
        status: values.status,
        payment_status: values.payment_status,
        end_date: values.end_date,
        auto_renew: values.auto_renew,
        notes: values.notes || null,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["subscriptions", id], updated)
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "all"] })
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "lookup"] })
      toast.success("Subscription updated successfully.")
      reset({
        status: updated.status,
        payment_status: updated.payment_status,
        end_date: updated.end_date,
        auto_renew: updated.auto_renew,
        notes: updated.notes ?? "",
      })
    },
  })

  if (subscriptionQuery.isLoading) {
    return <LoadingSpinner label="Loading subscription..." className="py-16" />
  }

  if (subscriptionQuery.isError || !subscriptionQuery.data) {
    return (
      <ErrorState
        title="Unable to load subscription"
        message={getApiErrorMessage(subscriptionQuery.error, "This subscription could not be found.")}
        onRetry={() => subscriptionQuery.refetch()}
      />
    )
  }

  const subscription = subscriptionQuery.data
  const clientName = clientQuery.data
    ? `${clientQuery.data.first_name} ${clientQuery.data.last_name}`
    : `Client #${subscription.client_id.slice(0, 8)}`

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/subscriptions" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to subscriptions
      </Button>

      <div>
        <h1 className="text-xl font-semibold">{subscription.plan_name}</h1>
        <p className="text-sm text-muted-foreground">
          {clientQuery.isLoading ? "Loading client..." : clientName}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Subscription Details</CardTitle>
          <CardDescription>Snapshot fields set at creation - immutable once the subscription exists.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Client</p>
            <p className="text-sm font-medium">{clientName}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Plan Name</p>
            <p className="text-sm font-medium">{subscription.plan_name}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Price</p>
            <p className="text-sm font-medium">{subscription.plan_price.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Currency</p>
            <p className="text-sm font-medium">{subscription.plan_currency}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Duration</p>
            <p className="text-sm font-medium">{subscription.plan_duration_days} days</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Sessions Per Week</p>
            <p className="text-sm font-medium">{subscription.plan_sessions_per_week ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Start Date</p>
            <p className="text-sm font-medium">{formatDate(subscription.start_date)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">End Date</p>
            <p className="text-sm font-medium">{formatDate(subscription.end_date)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Status</p>
            <Badge variant={SUBSCRIPTION_STATUS_BADGE_VARIANT[subscription.status]} className="mt-0.5">
              {SUBSCRIPTION_STATUS_LABELS[subscription.status]}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Payment Status</p>
            <Badge variant={SUBSCRIPTION_PAYMENT_STATUS_BADGE_VARIANT[subscription.payment_status]} className="mt-0.5">
              {SUBSCRIPTION_PAYMENT_STATUS_LABELS[subscription.payment_status]}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Auto Renew</p>
            <p className="text-sm font-medium">{subscription.auto_renew ? "Yes" : "No"}</p>
          </div>
          <div className="sm:col-span-2 lg:col-span-3">
            <p className="text-xs text-muted-foreground">Notes</p>
            <p className="text-sm font-medium whitespace-pre-wrap">{subscription.notes || "—"}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Update Subscription</CardTitle>
          <CardDescription>Change status, payment status, end date, auto-renew, or notes.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => updateMutation.mutate(values))} noValidate className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select id="status" aria-invalid={!!errors.status} {...register("status")}>
                  {STATUS_OPTIONS.map((status) => (
                    <option key={status} value={status}>
                      {SUBSCRIPTION_STATUS_LABELS[status]}
                    </option>
                  ))}
                </Select>
                {errors.status && <p className="text-sm text-destructive">{errors.status.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="payment_status">Payment Status</Label>
                <Select id="payment_status" aria-invalid={!!errors.payment_status} {...register("payment_status")}>
                  {PAYMENT_STATUS_OPTIONS.map((status) => (
                    <option key={status} value={status}>
                      {SUBSCRIPTION_PAYMENT_STATUS_LABELS[status]}
                    </option>
                  ))}
                </Select>
                {errors.payment_status && <p className="text-sm text-destructive">{errors.payment_status.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input id="end_date" type="date" aria-invalid={!!errors.end_date} {...register("end_date")} />
                {errors.end_date && <p className="text-sm text-destructive">{errors.end_date.message}</p>}
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

            {updateMutation.isError && (
              <ErrorState title="Couldn't update subscription" message={getApiErrorMessage(updateMutation.error)} />
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
