import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Ruler } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { MeasurementForm } from "@/app/pages/measurements/components/MeasurementForm"
import { measurementService } from "@/services/measurementService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import type { Measurement, MeasurementCreateInput, MeasurementUpdateInput } from "@/types/measurement"

const EDIT_WINDOW_EXPIRED_MESSAGE =
  "This measurement can no longer be modified. The configured edit window has expired."

const FIELDS: { key: keyof Measurement; label: string; unit: string }[] = [
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

interface MeasurementCardProps {
  clientId: string
  /** Auto-opens the Add or Edit form on mount, e.g. when arriving from the
   * Pending Measurements page's row actions. */
  initialAction?: "add" | "edit" | null
}

/** Latest-measurement section of a client's page - shows the most recent
 * recorded values, when they were last updated, and inline Add/Edit forms.
 * The edit window's length is an application setting only readable
 * server-side, so rather than predicting expiry client-side, edits are
 * always attempted and a 409 flips the card into a locked state (mirrors
 * SessionCheckInCard's handling of the same pattern for check-ins). */
export function MeasurementCard({ clientId, initialAction }: MeasurementCardProps) {
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<"view" | "add" | "edit">(
    initialAction === "add" ? "add" : initialAction === "edit" ? "edit" : "view",
  )
  const [editWindowExpired, setEditWindowExpired] = useState(false)

  const historyQuery = useQuery({
    queryKey: ["measurements", "client", clientId],
    queryFn: () => measurementService.getClientMeasurements(clientId),
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["measurements", "client", clientId] })
  }

  const createMutation = useMutation({
    mutationFn: (values: MeasurementUpdateInput) =>
      measurementService.create({
        client_id: clientId,
        recorded_at: null,
        ...values,
      } as MeasurementCreateInput),
    onSuccess: () => {
      invalidate()
      setMode("view")
      toast.success("Measurement recorded.")
    },
  })

  const updateMutation = useMutation({
    mutationFn: (values: MeasurementUpdateInput) => measurementService.update(historyQuery.data![0].id, values),
    onSuccess: () => {
      invalidate()
      setMode("view")
      toast.success("Measurement updated.")
    },
    onError: (error) => {
      if (getApiErrorMessage(error) === EDIT_WINDOW_EXPIRED_MESSAGE) {
        setEditWindowExpired(true)
        setMode("view")
      }
    },
  })

  if (historyQuery.isLoading) {
    return <LoadingSpinner label="Loading measurements..." className="py-8" />
  }

  if (historyQuery.isError) {
    return (
      <ErrorState
        title="Unable to load measurements"
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
            Latest Measurements
          </CardTitle>
          {latest && effectiveMode === "view" && (
            <Button size="sm" onClick={() => setMode("add")}>
              Add Measurement
            </Button>
          )}
        </div>
        <CardDescription>
          {latest ? `Last updated ${formatDateTime(latest.recorded_at)}` : "No measurements recorded yet."}
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
                Edit Measurement
              </Button>
            )}
          </>
        )}

        {effectiveMode === "view" && !latest && (
          <EmptyState
            icon={Ruler}
            message="No measurements recorded yet."
            action={
              <Button size="sm" onClick={() => setMode("add")}>
                Add Measurement
              </Button>
            }
          />
        )}

        {effectiveMode === "add" && (
          <MeasurementForm
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Save Measurement"
          />
        )}

        {effectiveMode === "edit" && latest && (
          <MeasurementForm
            measurement={latest}
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
