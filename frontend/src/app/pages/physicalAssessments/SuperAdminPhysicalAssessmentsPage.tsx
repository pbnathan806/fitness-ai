import { useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Pencil, Plus, Ruler, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { PhysicalAssessmentForm } from "@/app/pages/physicalAssessments/components/PhysicalAssessmentForm"
import { clientService } from "@/services/clientService"
import { physicalAssessmentService } from "@/services/physicalAssessmentService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import type { PhysicalAssessment, PhysicalAssessmentCreateInput, PhysicalAssessmentUpdateInput } from "@/types/physicalAssessment"

const PAGE_SIZE = 20

const EDIT_WINDOW_EXPIRED_MESSAGE =
  "This physical assessment can no longer be modified. The configured edit window has expired."

/** SUPER_ADMIN oversight over every recorded physical assessment: view all
 * (paginated), filter down to one client's full history, and edit any
 * record regardless of who recorded it (see backend
 * PhysicalAssessmentService.update_physical_assessment - SUPER_ADMIN may
 * edit any physical assessment, unlike TRAINER who is restricted to
 * assigned clients). */
export function SuperAdminPhysicalAssessmentsPage() {
  const queryClient = useQueryClient()
  const [clientFilter, setClientFilter] = useState("")
  const [page, setPage] = useState(1)
  const [editingPhysicalAssessment, setEditingPhysicalAssessment] = useState<PhysicalAssessment | null>(null)
  const [editWindowExpired, setEditWindowExpired] = useState(false)
  const [isAdding, setIsAdding] = useState(false)

  const clientsQuery = useQuery({ queryKey: ["clients", "all"], queryFn: clientService.listAllClients })

  const listQuery = useQuery({
    queryKey: ["physical-assessments", "list", page],
    queryFn: () => physicalAssessmentService.list(page, PAGE_SIZE),
    enabled: clientFilter === "",
  })

  const historyQuery = useQuery({
    queryKey: ["physical-assessments", "client", clientFilter],
    queryFn: () => physicalAssessmentService.getClientPhysicalAssessments(clientFilter),
    enabled: clientFilter !== "",
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  function invalidateActiveQuery() {
    if (clientFilter === "") {
      queryClient.invalidateQueries({ queryKey: ["physical-assessments", "list"] })
    } else {
      queryClient.invalidateQueries({ queryKey: ["physical-assessments", "client", clientFilter] })
    }
  }

  const createMutation = useMutation({
    mutationFn: (values: PhysicalAssessmentUpdateInput) =>
      physicalAssessmentService.create({
        client_id: clientFilter,
        recorded_at: null,
        ...values,
      } as PhysicalAssessmentCreateInput),
    onSuccess: () => {
      invalidateActiveQuery()
      setIsAdding(false)
      toast.success("Physical assessment recorded.")
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: string; values: PhysicalAssessmentUpdateInput }) =>
      physicalAssessmentService.update(id, values),
    onSuccess: () => {
      invalidateActiveQuery()
      setEditingPhysicalAssessment(null)
      toast.success("Physical assessment updated.")
    },
    onError: (error) => {
      if (getApiErrorMessage(error) === EDIT_WINDOW_EXPIRED_MESSAGE) {
        setEditWindowExpired(true)
        setEditingPhysicalAssessment(null)
      }
    },
  })

  const rows = clientFilter === "" ? (listQuery.data?.items ?? []) : (historyQuery.data ?? [])
  const isLoading = clientFilter === "" ? listQuery.isLoading : historyQuery.isLoading
  const isError = clientFilter === "" ? listQuery.isError : historyQuery.isError
  const activeError = clientFilter === "" ? listQuery.error : historyQuery.error
  const refetchActive = () => (clientFilter === "" ? listQuery.refetch() : historyQuery.refetch())
  const totalPages = clientFilter === "" ? (listQuery.data?.total_pages ?? 1) : 1

  function startEdit(physicalAssessment: PhysicalAssessment) {
    setEditWindowExpired(false)
    setIsAdding(false)
    setEditingPhysicalAssessment(physicalAssessment)
  }

  function startAdd() {
    setEditingPhysicalAssessment(null)
    setIsAdding(true)
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Physical Assessments</h1>
        <p className="text-sm text-muted-foreground">View every recorded physical assessment, or filter to one client's full history.</p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-xs w-full space-y-2">
          <Label htmlFor="client-filter">Filter by Client</Label>
          <Select
            id="client-filter"
            disabled={clientsQuery.isLoading}
            value={clientFilter}
            onChange={(e) => {
              setClientFilter(e.target.value)
              setPage(1)
              setEditingPhysicalAssessment(null)
              setIsAdding(false)
            }}
          >
            <option value="">All Clients</option>
            {(clientsQuery.data ?? []).map((client) => (
              <option key={client.id} value={client.id}>
                {client.first_name} {client.last_name} ({client.email})
              </option>
            ))}
          </Select>
        </div>
        <Button
          onClick={startAdd}
          disabled={clientFilter === ""}
          title={clientFilter === "" ? "Select a client first" : undefined}
        >
          <Plus className="size-4" />
          Add Physical Assessment
        </Button>
      </div>

      {isAdding && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Add Physical Assessment — {clientNameById.get(clientFilter) ?? "Client"}</CardTitle>
              <Button variant="ghost" size="icon-sm" aria-label="Cancel add" onClick={() => setIsAdding(false)}>
                <X className="size-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <PhysicalAssessmentForm
              onSubmit={(values) => createMutation.mutate(values)}
              isSubmitting={createMutation.isPending}
              submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
              submitLabel="Save Physical Assessment"
            />
          </CardContent>
        </Card>
      )}

      {editingPhysicalAssessment && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>
                Edit Physical Assessment — {clientNameById.get(editingPhysicalAssessment.client_id) ?? "Unknown Client"}
              </CardTitle>
              <Button variant="ghost" size="icon-sm" aria-label="Cancel edit" onClick={() => setEditingPhysicalAssessment(null)}>
                <X className="size-4" />
              </Button>
            </div>
            <CardDescription>Recorded {formatDate(editingPhysicalAssessment.recorded_at)}</CardDescription>
          </CardHeader>
          <CardContent>
            <PhysicalAssessmentForm
              physicalAssessment={editingPhysicalAssessment}
              onSubmit={(values) => updateMutation.mutate({ id: editingPhysicalAssessment.id, values })}
              isSubmitting={updateMutation.isPending}
              submitErrorMessage={
                updateMutation.isError && getApiErrorMessage(updateMutation.error) !== EDIT_WINDOW_EXPIRED_MESSAGE
                  ? getApiErrorMessage(updateMutation.error)
                  : null
              }
              submitLabel="Save Changes"
            />
          </CardContent>
        </Card>
      )}

      {editWindowExpired && (
        <ErrorState title="Edit window expired" message={EDIT_WINDOW_EXPIRED_MESSAGE} />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ruler className="size-4 text-muted-foreground" aria-hidden="true" />
            {clientFilter === "" ? "All Physical Assessments" : `History for ${clientNameById.get(clientFilter) ?? "Client"}`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!isLoading && isError && (
            <ErrorState
              message={getApiErrorMessage(activeError, "Unable to load physical assessments.")}
              onRetry={refetchActive}
            />
          )}

          {!isLoading && !isError && rows.length === 0 && (
            <EmptyState icon={Ruler} message="No physical assessments found." />
          )}

          {!isLoading && !isError && rows.length > 0 && (
            <div className="space-y-3">
              <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                    <tr>
                      {clientFilter === "" && <th className="px-3 py-2 font-medium">Client</th>}
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">Weight</th>
                      <th className="px-3 py-2 font-medium">Body Fat</th>
                      <th className="px-3 py-2 font-medium">Waist</th>
                      <th className="px-3 py-2 font-medium">Chest</th>
                      <th className="px-3 py-2 font-medium">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {rows.map((physicalAssessment) => (
                      <tr key={physicalAssessment.id} className="hover:bg-muted/30">
                        {clientFilter === "" && (
                          <td className="max-w-[200px] truncate px-3 py-2.5 font-medium">
                            {clientNameById.get(physicalAssessment.client_id) ?? `Client #${physicalAssessment.client_id.slice(0, 8)}`}
                          </td>
                        )}
                        <td className="px-3 py-2.5 whitespace-nowrap">{formatDate(physicalAssessment.recorded_at)}</td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {physicalAssessment.weight_kg != null ? `${physicalAssessment.weight_kg} kg` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {physicalAssessment.body_fat_percentage != null ? `${physicalAssessment.body_fat_percentage} %` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {physicalAssessment.waist_cm != null ? `${physicalAssessment.waist_cm} cm` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {physicalAssessment.chest_cm != null ? `${physicalAssessment.chest_cm} cm` : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            aria-label="Edit physical assessment"
                            onClick={() => startEdit(physicalAssessment)}
                          >
                            <Pencil className="size-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {clientFilter === "" && totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
