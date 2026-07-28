import { useState } from "react"
import { Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { TrainerTable } from "@/app/pages/trainers/components/TrainerTable"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SortDirection, Trainer, TrainerListSortBy } from "@/types/trainer"

const PAGE_SIZE = 10

const STATUS_FILTER_OPTIONS = ["ALL", "ACTIVE", "INACTIVE"] as const

const SORT_OPTIONS: { value: `${TrainerListSortBy}:${SortDirection}`; label: string }[] = [
  { value: "created_at:desc", label: "Newest first" },
  { value: "created_at:asc", label: "Oldest first" },
  { value: "first_name:asc", label: "First name (A-Z)" },
  { value: "first_name:desc", label: "First name (Z-A)" },
]

export function TrainersListPage() {
  const queryClient = useQueryClient()
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [statusFilter, setStatusFilter] = useState<(typeof STATUS_FILTER_OPTIONS)[number]>("ALL")
  const [sort, setSort] = useState<`${TrainerListSortBy}:${SortDirection}`>("created_at:desc")
  const [page, setPage] = useState(1)

  const [sortBy, sortDir] = sort.split(":") as [TrainerListSortBy, SortDirection]
  const isActive = statusFilter === "ALL" ? undefined : statusFilter === "ACTIVE"

  const trainersQuery = useQuery({
    queryKey: ["trainers", "list", { page, firstName, lastName, email, isActive, sortBy, sortDir }],
    queryFn: () =>
      trainerService.listTrainers({
        page,
        page_size: PAGE_SIZE,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        email: email || undefined,
        is_active: isActive,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
    placeholderData: (previous) => previous,
  })

  const statusMutation = useMutation({
    mutationFn: (trainer: Trainer) => trainerService.updateTrainerStatus(trainer.id, !trainer.is_active),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["trainers"] })
      toast.success(updated.is_active ? "Trainer activated." : "Trainer deactivated.")
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to update trainer status."))
    },
  })

  function handleToggleStatus(trainer: Trainer) {
    const action = trainer.is_active ? "deactivate" : "activate"
    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${trainer.first_name} ${trainer.last_name}?`,
    )
    if (confirmed) {
      statusMutation.mutate(trainer)
    }
  }

  function resetToFirstPage() {
    setPage(1)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Trainers</h1>
          <p className="text-sm text-muted-foreground">Manage trainer profiles.</p>
        </div>
        <Button render={<Link to="/super-admin/trainers/new" />} nativeButton={false}>
          <Plus className="size-4" />
          New Trainer
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Search &amp; Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="trainer-search-first-name">First Name</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="trainer-search-first-name"
                  placeholder="Search first name"
                  className="pl-7"
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(e.target.value)
                    resetToFirstPage()
                  }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trainer-search-last-name">Last Name</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="trainer-search-last-name"
                  placeholder="Search last name"
                  className="pl-7"
                  value={lastName}
                  onChange={(e) => {
                    setLastName(e.target.value)
                    resetToFirstPage()
                  }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trainer-search-email">Email</Label>
              <div className="relative">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="trainer-search-email"
                  placeholder="Search email"
                  className="pl-7"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    resetToFirstPage()
                  }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="trainer-status-filter">Status</Label>
              <Select
                id="trainer-status-filter"
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as (typeof STATUS_FILTER_OPTIONS)[number])
                  resetToFirstPage()
                }}
              >
                {STATUS_FILTER_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status === "ALL" ? "All statuses" : status === "ACTIVE" ? "Active" : "Inactive"}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="space-y-1.5 sm:max-w-xs">
            <Label htmlFor="trainer-sort">Sort by</Label>
            <Select
              id="trainer-sort"
              value={sort}
              onChange={(e) => {
                setSort(e.target.value as `${TrainerListSortBy}:${SortDirection}`)
                resetToFirstPage()
              }}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>

          {trainersQuery.isError && (
            <p className="text-xs text-destructive">{getApiErrorMessage(trainersQuery.error, "Unable to load trainers.")}</p>
          )}
        </CardContent>
      </Card>

      <TrainerTable
        rows={trainersQuery.data?.items ?? []}
        isLoading={trainersQuery.isLoading}
        isError={trainersQuery.isError}
        onRetry={() => trainersQuery.refetch()}
        page={trainersQuery.data?.page ?? page}
        totalPages={trainersQuery.data?.total_pages ?? 1}
        onPageChange={setPage}
        onToggleStatus={handleToggleStatus}
        pendingStatusTrainerId={statusMutation.isPending ? statusMutation.variables?.id : null}
      />
    </div>
  )
}
