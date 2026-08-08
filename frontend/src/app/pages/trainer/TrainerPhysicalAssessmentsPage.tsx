import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Ruler, Eye, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { PhysicalAssessmentForm } from "@/app/pages/physicalAssessments/components/PhysicalAssessmentForm"
import { physicalAssessmentService } from "@/services/physicalAssessmentService"
import { assignmentService } from "@/services/assignmentService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import type { PhysicalAssessmentCreateInput, PhysicalAssessmentUpdateInput } from "@/types/physicalAssessment"

type Tab = "pending" | "never-assessed" | "all"

/** Trainer's own physical assessments: a Pending queue (assigned clients
 * overdue for their next physical assessment), a Never Assessed queue
 * (assigned clients with zero physical assessments on record - a distinct
 * bucket from Pending, which only covers clients who have at least one
 * stale record), and an All log (every recorded physical assessment for
 * assigned clients, newest first). A standalone quick-add picker above the
 * tabs lets a trainer jump straight to adding a physical assessment for any
 * assigned client, regardless of which tab is active - it doesn't filter or
 * change the tabs, it's purely a fast path for "I'm with this client right
 * now." Client identity throughout is resolved via the trainer's own
 * assigned-clients roster (name only, no PII) rather than GET /clients -
 * trainers must not see a client's email or phone number anywhere in the
 * trainer-facing UI. */
export function TrainerPhysicalAssessmentsPage() {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>("pending")
  const [quickAddClientId, setQuickAddClientId] = useState("")
  const [isQuickAdding, setIsQuickAdding] = useState(false)

  const clientsQuery = useQuery({
    queryKey: ["assignments", "my-clients"],
    queryFn: assignmentService.getMyClients,
  })

  // Always fetched (not gated by tab) since overdue_threshold_days drives
  // the top-of-page note regardless of which tab is active.
  const pendingQuery = useQuery({
    queryKey: ["physical-assessments", "pending"],
    queryFn: physicalAssessmentService.listPending,
  })

  const allQuery = useQuery({
    queryKey: ["physical-assessments", "all"],
    queryFn: physicalAssessmentService.listAllPhysicalAssessments,
    enabled: tab === "all" || tab === "never-assessed",
  })

  const clientNameById = useMemo(() => {
    const map = new Map<string, string>()
    for (const client of clientsQuery.data ?? []) {
      map.set(client.client_id, `${client.first_name} ${client.last_name}`)
    }
    return map
  }, [clientsQuery.data])

  const sortedPhysicalAssessments = useMemo(() => {
    return [...(allQuery.data ?? [])].sort(
      (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime(),
    )
  }, [allQuery.data])

  const neverAssessedClients = useMemo(() => {
    if (!allQuery.data) return []
    const assessedClientIds = new Set(allQuery.data.map((item) => item.client_id))
    return (clientsQuery.data ?? []).filter((client) => !assessedClientIds.has(client.client_id))
  }, [clientsQuery.data, allQuery.data])

  const allIsLoading = allQuery.isLoading || clientsQuery.isLoading
  const allIsError = allQuery.isError
  const neverAssessedIsLoading = clientsQuery.isLoading || allQuery.isLoading
  const neverAssessedIsError = clientsQuery.isError || allQuery.isError

  function invalidatePhysicalAssessmentQueries() {
    queryClient.invalidateQueries({ queryKey: ["physical-assessments", "pending"] })
    queryClient.invalidateQueries({ queryKey: ["physical-assessments", "all"] })
  }

  const quickAddMutation = useMutation({
    mutationFn: (values: PhysicalAssessmentUpdateInput) =>
      physicalAssessmentService.create({
        client_id: quickAddClientId,
        recorded_at: null,
        ...values,
      } as PhysicalAssessmentCreateInput),
    onSuccess: () => {
      invalidatePhysicalAssessmentQueries()
      setIsQuickAdding(false)
      setQuickAddClientId("")
      toast.success("Physical assessment recorded.")
    },
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Physical Assessments</h1>
        <p className="text-sm text-muted-foreground">Physical assessments for your assigned clients.</p>
        {pendingQuery.data && (
          <p className="mt-1 text-sm text-muted-foreground">
            A physical assessment is expected every{" "}
            <span className="font-medium text-foreground">{pendingQuery.data.overdue_threshold_days} days</span>.
            <span className="text-xs"> Pending shows how many days it's been since each client's last one.</span>
          </p>
        )}
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 pt-4 sm:flex-row sm:items-end">
          <div className="w-full space-y-2 sm:max-w-xs">
            <Label htmlFor="quick-add-client">Add Physical Assessment For</Label>
            <Select
              id="quick-add-client"
              disabled={clientsQuery.isLoading}
              value={quickAddClientId}
              onChange={(e) => {
                setQuickAddClientId(e.target.value)
                setIsQuickAdding(false)
              }}
            >
              <option value="">Select a client</option>
              {(clientsQuery.data ?? []).map((client) => (
                <option key={client.client_id} value={client.client_id}>
                  {client.first_name} {client.last_name}
                </option>
              ))}
            </Select>
          </div>
          <Button
            onClick={() => setIsQuickAdding(true)}
            disabled={quickAddClientId === "" || isQuickAdding}
            className="sm:w-auto"
          >
            Add
          </Button>
        </CardContent>
      </Card>

      {isQuickAdding && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Add Physical Assessment — {clientNameById.get(quickAddClientId) ?? "Client"}</CardTitle>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Cancel add"
                onClick={() => setIsQuickAdding(false)}
              >
                <X className="size-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <PhysicalAssessmentForm
              onSubmit={(values) => quickAddMutation.mutate(values)}
              isSubmitting={quickAddMutation.isPending}
              submitErrorMessage={quickAddMutation.isError ? getApiErrorMessage(quickAddMutation.error) : null}
              submitLabel="Save Physical Assessment"
            />
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2">
        <Button variant={tab === "pending" ? "default" : "outline"} size="sm" onClick={() => setTab("pending")}>
          Pending
        </Button>
        <Button
          variant={tab === "never-assessed" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("never-assessed")}
        >
          Never Assessed
        </Button>
        <Button variant={tab === "all" ? "default" : "outline"} size="sm" onClick={() => setTab("all")}>
          All
        </Button>
      </div>

      {tab === "pending" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Pending Physical Assessments</CardTitle>
              {!pendingQuery.isLoading && !pendingQuery.isError && (
                <Badge variant={pendingQuery.data && pendingQuery.data.items.length > 0 ? "warning" : "secondary"}>
                  {pendingQuery.data?.items.length ?? 0} pending
                </Badge>
              )}
            </div>
            <CardDescription>
              Client list: assigned clients who already have at least one physical assessment on
              record, but their most recent one is now overdue (more than{" "}
              {pendingQuery.data?.overdue_threshold_days ?? "—"} days ago).
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingQuery.isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            )}

            {!pendingQuery.isLoading && pendingQuery.isError && (
              <ErrorState message={getApiErrorMessage(pendingQuery.error)} onRetry={() => pendingQuery.refetch()} />
            )}

            {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data?.items.length === 0 && (
              <EmptyState icon={Ruler} message="No pending physical assessments. Everything is up to date." />
            )}

            {!pendingQuery.isLoading && !pendingQuery.isError && pendingQuery.data && pendingQuery.data.items.length > 0 && (
              <ul className="divide-y">
                {pendingQuery.data.items.map((item) => (
                  <li key={item.client_id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between gap-3">
                      <Link to={`/trainer/clients/${item.client_id}`} className="min-w-0 flex-1 hover:underline">
                        <p className="text-sm font-medium">{item.client_name}</p>
                        <p className="text-xs text-muted-foreground">
                          Last assessed {formatDate(item.last_physical_assessment_date)}
                        </p>
                      </Link>
                      <Badge variant="warning" className="shrink-0">
                        {item.days_overdue} day{item.days_overdue === 1 ? "" : "s"} overdue
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        render={<Link to={`/trainer/clients/${item.client_id}?action=add`} />}
                        nativeButton={false}
                      >
                        Add Physical Assessment
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        render={<Link to={`/trainer/clients/${item.client_id}?action=edit`} />}
                        nativeButton={false}
                      >
                        Edit Physical Assessment
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        render={<Link to={`/trainer/clients/${item.client_id}`} />}
                        nativeButton={false}
                      >
                        View History
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "never-assessed" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Never Assessed</CardTitle>
              {!neverAssessedIsLoading && !neverAssessedIsError && (
                <Badge variant={neverAssessedClients.length > 0 ? "warning" : "secondary"}>
                  {neverAssessedClients.length} client{neverAssessedClients.length === 1 ? "" : "s"}
                </Badge>
              )}
            </div>
            <CardDescription>
              Client list: assigned clients who have never had a single physical assessment recorded
              - distinct from Pending, which only covers clients who have at least one, now stale, record.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {neverAssessedIsLoading && (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            )}

            {!neverAssessedIsLoading && neverAssessedIsError && (
              <ErrorState
                message="Unable to load clients."
                onRetry={() => {
                  clientsQuery.refetch()
                  allQuery.refetch()
                }}
              />
            )}

            {!neverAssessedIsLoading && !neverAssessedIsError && neverAssessedClients.length === 0 && (
              <EmptyState icon={Ruler} message="Every assigned client has at least one physical assessment on record." />
            )}

            {!neverAssessedIsLoading && !neverAssessedIsError && neverAssessedClients.length > 0 && (
              <ul className="divide-y">
                {neverAssessedClients.map((client) => (
                  <li key={client.assignment_id} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                    <p className="text-sm font-medium">
                      {client.first_name} {client.last_name}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      render={<Link to={`/trainer/clients/${client.client_id}?action=add`} />}
                      nativeButton={false}
                    >
                      Add Physical Assessment
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "all" && (
        <Card>
          <CardHeader>
            <CardTitle>All Physical Assessments</CardTitle>
            <CardDescription>
              Record list, not a client list: every individual physical assessment ever recorded for
              your assigned clients, newest first. A client can appear more than once here (one row
              per assessment) or not at all if they're in Never Assessed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {allIsLoading && (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            )}

            {!allIsLoading && allIsError && (
              <ErrorState
                message={getApiErrorMessage(allQuery.error, "Unable to load physical assessments.")}
                onRetry={() => allQuery.refetch()}
              />
            )}

            {!allIsLoading && !allIsError && sortedPhysicalAssessments.length === 0 && (
              <EmptyState icon={Ruler} message="No physical assessments found." />
            )}

            {!allIsLoading && !allIsError && sortedPhysicalAssessments.length > 0 && (
              <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Client</th>
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
                    {sortedPhysicalAssessments.map((physicalAssessment) => (
                      <tr key={physicalAssessment.id} className="hover:bg-muted/30">
                        <td className="max-w-[180px] truncate px-3 py-2.5 font-medium">
                          {clientNameById.get(physicalAssessment.client_id) ?? `Client #${physicalAssessment.client_id.slice(0, 8)}`}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                          {formatDate(physicalAssessment.recorded_at)}
                        </td>
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
                        <td className="px-3 py-2.5 text-right whitespace-nowrap">
                          <Button
                            variant="ghost"
                            size="sm"
                            render={<Link to={`/trainer/clients/${physicalAssessment.client_id}`} />}
                            nativeButton={false}
                          >
                            <Eye className="size-4" />
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
