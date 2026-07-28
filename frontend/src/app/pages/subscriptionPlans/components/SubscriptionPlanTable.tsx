import { useNavigate } from "react-router-dom"
import { MoreHorizontal, Eye, Pencil, Package } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { buttonVariants } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import type { SubscriptionPlan } from "@/types/subscription"

interface SubscriptionPlanTableProps {
  plans: SubscriptionPlan[]
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

function formatPrice(price: number, currency: string): string {
  return `${currency} ${price.toFixed(2)}`
}

/** Reusable subscription plan table (Task 22.5). There is no dedicated plan
 * "details" route in this module - View and Edit both open the Edit screen,
 * which already renders every field (immutable ones disabled) and so doubles
 * as a read-only view. */
export function SubscriptionPlanTable({ plans, isLoading, isError, onRetry }: SubscriptionPlanTableProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load subscription plans"
        message="Something went wrong while loading subscription plans."
        onRetry={onRetry}
      />
    )
  }

  if (plans.length === 0) {
    return <EmptyState icon={Package} message="No subscription plans found." />
  }

  return (
    <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Name</th>
            <th className="px-3 py-2 font-medium">Duration (Days)</th>
            <th className="px-3 py-2 font-medium">Price</th>
            <th className="px-3 py-2 font-medium">Currency</th>
            <th className="px-3 py-2 font-medium">Sessions Per Week</th>
            <th className="px-3 py-2 font-medium">Max Sessions Per Month</th>
            <th className="px-3 py-2 font-medium">Active</th>
            <th className="px-3 py-2 font-medium">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {plans.map((plan) => (
            <tr key={plan.id} className="hover:bg-muted/30">
              <td className="max-w-[220px] truncate px-3 py-2.5 font-medium">{plan.name}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{plan.duration_days}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{formatPrice(plan.price, plan.currency)}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{plan.currency}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{plan.sessions_per_week ?? "—"}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{plan.max_sessions_per_month ?? "—"}</td>
              <td className="px-3 py-2.5">
                <Badge variant={plan.is_active ? "success" : "secondary"}>
                  {plan.is_active ? "Active" : "Inactive"}
                </Badge>
              </td>
              <td className="px-3 py-2.5 text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger
                    className={cn(buttonVariants({ variant: "ghost", size: "icon-sm" }))}
                    aria-label="Subscription plan actions"
                  >
                    <MoreHorizontal className="size-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => navigate(`/super-admin/subscription-plans/${plan.id}/edit`)}>
                      <Eye className="size-4" />
                      View Plan
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate(`/super-admin/subscription-plans/${plan.id}/edit`)}>
                      <Pencil className="size-4" />
                      Edit Plan
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
