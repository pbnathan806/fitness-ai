import { Link, useNavigate } from "react-router-dom"
import { MoreHorizontal, Eye, Pencil, UserCog, CreditCard, CalendarDays, ChevronLeft, ChevronRight, Users } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button, buttonVariants } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDate } from "@/lib/format"
import { SUBSCRIPTION_STATUS_BADGE_VARIANT, SUBSCRIPTION_STATUS_LABELS } from "@/lib/subscriptionStatus"
import type { SubscriptionStatusValue } from "@/lib/subscriptionStatus"
import type { Client } from "@/types/client"

export interface ClientRow {
  client: Client
  trainerCount: number
  subscriptionStatus: SubscriptionStatusValue
}

interface ClientTableProps {
  rows: ClientRow[]
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

/** Reusable client list table for the Clients Module (Task 22.3). Pagination
 * is client-side (see clientService.listAllClients) - the backend's
 * `GET /clients` has no search/filter query params, so the full list is
 * fetched once and filtered/paginated in the browser. */
export function ClientTable({ rows, isLoading, isError, onRetry, page, totalPages, onPageChange }: ClientTableProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return <ErrorState title="Unable to load clients" message="Something went wrong while loading clients." onRetry={onRetry} />
  }

  if (rows.length === 0) {
    return <EmptyState icon={Users} message="No clients found." />
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Email</th>
              <th className="px-3 py-2 font-medium">Subscription Status</th>
              <th className="px-3 py-2 font-medium">Assigned Trainers</th>
              <th className="px-3 py-2 font-medium">Created Date</th>
              <th className="px-3 py-2 font-medium">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map(({ client, trainerCount, subscriptionStatus }) => (
              <tr key={client.id} className="hover:bg-muted/30">
                <td className="max-w-[200px] truncate px-3 py-2.5 font-medium">
                  <Link to={`/super-admin/clients/${client.id}`} className="hover:underline">
                    {client.first_name} {client.last_name}
                  </Link>
                </td>
                <td className="max-w-[220px] truncate px-3 py-2.5 text-muted-foreground">{client.email}</td>
                <td className="px-3 py-2.5">
                  <Badge variant={SUBSCRIPTION_STATUS_BADGE_VARIANT[subscriptionStatus]}>
                    {SUBSCRIPTION_STATUS_LABELS[subscriptionStatus]}
                  </Badge>
                </td>
                <td className="px-3 py-2.5 text-muted-foreground">
                  {trainerCount} {trainerCount === 1 ? "trainer" : "trainers"}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{formatDate(client.created_at)}</td>
                <td className="px-3 py-2.5 text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger
                      className={cn(buttonVariants({ variant: "ghost", size: "icon-sm" }))}
                      aria-label="Client actions"
                    >
                      <MoreHorizontal className="size-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => navigate(`/super-admin/clients/${client.id}`)}>
                        <Eye className="size-4" />
                        View Client
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate(`/super-admin/clients/${client.id}/edit`)}>
                        <Pencil className="size-4" />
                        Edit Client
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate(`/super-admin/clients/${client.id}/trainers`)}>
                        <UserCog className="size-4" />
                        Manage Trainers
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/super-admin/subscriptions")}>
                        <CreditCard className="size-4" />
                        View Subscriptions
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/super-admin/sessions")}>
                        <CalendarDays className="size-4" />
                        View Sessions
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              <ChevronLeft className="size-4" />
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              Next
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
