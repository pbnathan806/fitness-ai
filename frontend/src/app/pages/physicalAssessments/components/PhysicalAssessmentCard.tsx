import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Ruler } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { PhysicalAssessmentForm } from "@/app/pages/physicalAssessments/components/PhysicalAssessmentForm"
import { physicalAssessmentService } from "@/services/physicalAssessmentService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import type { PhysicalAssessment, PhysicalAssessmentCreateInput, PhysicalAssessmentUpdateInput } from "@/types/physicalAssessment"

const EDIT_WINDOW_EXPIRED_MESSAGE =
  "This physical assessment can no longer be modified. The configured edit window has expired."

const FIELDS: { key: keyof PhysicalAssessment; label: string; unit: string }[] = [
  { key: "weight_kg", label: "Weight", unit: "kg" },
  { key: "body_fat_percentage", label: "Body Fat", unit: "%" },
  { key: "chest_cm", label: "Chest", unit: "cm" },
  { key: "waist_cm", label: "Waist", unit: "cm" },
  { key: "hips_cm", label: "Hips", unit: "cm" },
  { key: "left_arm_cm", label: "Left Arm", unit: "cm" },
  { key: "right_arm_cm", label: "Right Arm", unit: "cm" },
  { key: "left_thigh_cm", label: "Left Thigh", unit: "cm" },
  { key: "right_thigh_cm", label: "Right Thigh", unit: "cm" },
  { key: "resting_heart_rate", label: "Resting Heart Rate", unit: "bpm" },
]

interface PhysicalAssessmentCardProps {
  clientId: string
  /** Auto-opens the Add or Edit form on mount, e.g. when arriving from the
   * Pending Physical Assessments page's row actions. */
  initialAction?: "add" | "edit" | null
}

/** Latest-physical-assessment section of a client's page - shows the most
 * recent recorded values, when they were last updated, and inline Add/Edit
 * forms. The edit window's length is an application setting only readable
 * server-side, so rather than predicting expiry client-side, edits are
 * always attempted and a 409 flips the card into a locked state (mirrors
 * SessionCheckInCard's handling of the same pattern for check-ins). */
export function PhysicalAssessmentCard({ clientId, initialAction }: PhysicalAssessmentCardProps) {
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<"view" | "add" | "edit">(
    initialAction === "add" ? "add" : initialAction === "edit" ? "edit" : "view",
  )
  const [editWindowExpired, setEditWindowExpired] = useState(false)

  const historyQuery = useQuery({
    queryKey: ["physical-assessments", "client", clientId],
    queryFn: () => physicalAssessmentService.getClientPhysicalAssessments(clientId),
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["physical-assessments", "client", clientId] })
  }

  const createMutation = useMutation({
    mutationFn: (values: PhysicalAssessmentUpdateInput) =>
      physicalAssessmentService.create({
        client_id: clientId,
        recorded_at: null,
        ...values,
      } as PhysicalAssessmentCreateInput),
    onSuccess: () => {
      invalidate()
      setMode("view")
      toast.success("Physical assessment recorded.")
    },
  })

  const updateMutation = useMutation({
    mutationFn: (values: PhysicalAssessmentUpdateInput) =>
      physicalAssessmentService.update(historyQuery.data![0].id, values),
    onSuccess: () => {
      invalidate()
      setMode("view")
      toast.success("Physical assessment updated.")
    },
    onError: (error) => {
      if (getApiErrorMessage(error) === EDIT_WINDOW_EXPIRED_MESSAGE) {
        setEditWindowExpired(true)
        setMode("view")
      }
    },
  })

  if (historyQuery.isLoading) {
    return <LoadingSpinner label="Loading physical assessments..." className="py-8" />
  }

  if (historyQuery.isError) {
    return (
      <ErrorState
        title="Unable to load physical assessments"
        message={getApiErrorMessage(historyQuery.error)}
        onRetry={() => historyQuery.refetch()}
      />
    )
  }

  const history = historyQuery.data ?? []
  const latest = history[0]
  const effectiveMode = mode === "edit" && !latest ? "view" : mode

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2">
            <Ruler className="size-4 text-muted-foreground" aria-hidden="true" />
            Latest Physical Assessment
          </CardTitle>
          {latest && effectiveMode === "view" && (
            <Button size="sm" onClick={() => setMode("add")}>
              Add Physical Assessment
            </Button>
          )}
        </div>
        <CardDescription>
          {latest ? `Last updated ${formatDateTime(latest.recorded_at)}` : "No physical assessments recorded yet."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {effectiveMode === "view" && latest && (
          <>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {FIELDS.map((field) => (
                <div key={field.key}>
                  <dt className="text-xs text-muted-foreground">{field.label}</dt>
                  <dd className="text-sm font-medium">
                    {latest[field.key] != null ? `${latest[field.key]} ${field.unit}` : "—"}
                  </dd>
                </div>
              ))}
            </dl>

            {editWindowExpired ? (
              <ErrorState title="Edit window expired" message={EDIT_WINDOW_EXPIRED_MESSAGE} />
            ) : (
              <Button variant="outline" size="sm" onClick={() => setMode("edit")}>
                Edit Physical Assessment
              </Button>
            )}
          </>
        )}

        {effectiveMode === "view" && !latest && (
          <EmptyState
            icon={Ruler}
            message="No physical assessments recorded yet."
            action={
              <Button size="sm" onClick={() => setMode("add")}>
                Add Physical Assessment
              </Button>
            }
          />
        )}

        {effectiveMode === "add" && (
          <PhysicalAssessmentForm
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Save Physical Assessment"
          />
        )}

        {effectiveMode === "edit" && latest && (
          <PhysicalAssessmentForm
            physicalAssessment={latest}
            onSubmit={(values) => updateMutation.mutate(values)}
            isSubmitting={updateMutation.isPending}
            submitErrorMessage={
              updateMutation.isError && getApiErrorMessage(updateMutation.error) !== EDIT_WINDOW_EXPIRED_MESSAGE
                ? getApiErrorMessage(updateMutation.error)
                : null
            }
            submitLabel="Save Changes"
          />
        )}

        {(effectiveMode === "add" || (effectiveMode === "edit" && latest)) && (
          <Button variant="ghost" size="sm" onClick={() => setMode("view")}>
            Cancel
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
