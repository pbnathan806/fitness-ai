import { Link, useNavigate } from "react-router-dom"
import { MoreHorizontal, Eye, Pencil, UserCog, ChevronLeft, ChevronRight, Ban, CheckCircle2 } from "lucide-react"
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
import type { Trainer } from "@/types/trainer"

interface TrainerTableProps {
  rows: Trainer[]
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  onToggleStatus: (trainer: Trainer) => void
  /** Id of the trainer whose status change is in flight, so its row's action
   * can be disabled without blocking the rest of the table. */
  pendingStatusTrainerId?: string | null
}

/** Trainer directory table (Task 22.4.1), backed by the real
 * `GET /trainers` endpoint (search/filter/sort/pagination all server-side -
 * see TrainersListPage). */
export function TrainerTable({
  rows,
  isLoading,
  isError,
  onRetry,
  page,
  totalPages,
  onPageChange,
  onToggleStatus,
  pendingStatusTrainerId,
}: TrainerTableProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="space-y-2" role="status" aria-label="Loading trainers...">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return <ErrorState title="Unable to load trainers" message="Something went wrong while loading trainers." onRetry={onRetry} />
  }

  if (rows.length === 0) {
    return <EmptyState icon={UserCog} message="No trainers found." />
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Email</th>
              <th className="px-3 py-2 font-medium">Phone</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Created Date</th>
              <th className="px-3 py-2 font-medium">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((trainer) => (
              <tr key={trainer.id} className="hover:bg-muted/30">
                <td className="max-w-[200px] truncate px-3 py-2.5 font-medium">
                  <Link to={`/super-admin/trainers/${trainer.id}`} className="hover:underline">
                    {trainer.first_name} {trainer.last_name}
                  </Link>
                </td>
                <td className="max-w-[220px] truncate px-3 py-2.5 text-muted-foreground">{trainer.email}</td>
                <td className="px-3 py-2.5 text-muted-foreground">{trainer.phone_number ?? "—"}</td>
                <td className="px-3 py-2.5">
                  <Badge variant={trainer.is_active ? "success" : "secondary"}>
                    {trainer.is_active ? "Active" : "Inactive"}
                  </Badge>
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{formatDate(trainer.created_at)}</td>
                <td className="px-3 py-2.5 text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger
                      className={cn(buttonVariants({ variant: "ghost", size: "icon-sm" }))}
                      aria-label="Trainer actions"
                    >
                      <MoreHorizontal className="size-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => navigate(`/super-admin/trainers/${trainer.id}`)}>
                        <Eye className="size-4" />
                        View Trainer
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate(`/super-admin/trainers/${trainer.id}/edit`)}>
                        <Pencil className="size-4" />
                        Edit Trainer
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        disabled={pendingStatusTrainerId === trainer.id}
                        onClick={() => onToggleStatus(trainer)}
                      >
                        {trainer.is_active ? (
                          <>
                            <Ban className="size-4" />
                            Deactivate Trainer
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="size-4" />
                            Activate Trainer
                          </>
                        )}
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
