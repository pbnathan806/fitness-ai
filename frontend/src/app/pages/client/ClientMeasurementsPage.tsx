import { useQuery } from "@tanstack/react-query"
import { Ruler } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { clientService } from "@/services/clientService"
import { measurementService } from "@/services/measurementService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import type { LatestMeasurement } from "@/types/measurement"

interface FieldSpec {
  key: keyof LatestMeasurement
  previousKey: keyof LatestMeasurement
  changeKey: keyof LatestMeasurement
  label: string
  unit: string
}

const FIELDS: FieldSpec[] = [
  { key: "weight_kg", previousKey: "previous_weight_kg", changeKey: "weight_change", label: "Weight", unit: "kg" },
  {
    key: "body_fat_percentage",
    previousKey: "previous_body_fat_percentage",
    changeKey: "body_fat_change",
    label: "Body Fat",
    unit: "%",
  },
  { key: "chest_cm", previousKey: "previous_chest_cm", changeKey: "chest_change", label: "Chest", unit: "cm" },
  { key: "waist_cm", previousKey: "previous_waist_cm", changeKey: "waist_change", label: "Waist", unit: "cm" },
  { key: "hips_cm", previousKey: "previous_hips_cm", changeKey: "hips_change", label: "Hips", unit: "cm" },
  {
    key: "left_arm_cm",
    previousKey: "previous_left_arm_cm",
    changeKey: "left_arm_change",
    label: "Left Arm",
    unit: "cm",
  },
  {
    key: "right_arm_cm",
    previousKey: "previous_right_arm_cm",
    changeKey: "right_arm_change",
    label: "Right Arm",
    unit: "cm",
  },
  {
    key: "left_thigh_cm",
    previousKey: "previous_left_thigh_cm",
    changeKey: "left_thigh_change",
    label: "Left Thigh",
    unit: "cm",
  },
  {
    key: "right_thigh_cm",
    previousKey: "previous_right_thigh_cm",
    changeKey: "right_thigh_change",
    label: "Right Thigh",
    unit: "cm",
  },
  {
    key: "resting_heart_rate",
    previousKey: "previous_resting_heart_rate",
    changeKey: "resting_heart_rate_change",
    label: "Resting Heart Rate",
    unit: "bpm",
  },
]

/** "72 -> 70 kg (-2)" when both a current and a previous value exist; just
 * the current value on a client's first-ever measurement (no previous to
 * compare against); "Not recorded" when the field has never been captured. */
function formatMetric(current: number | null, previous: number | null, change: number | null, unit: string): string {
  if (current == null) return "Not recorded"
  if (previous == null) return `${current} ${unit}`
  const sign = change != null && change > 0 ? "+" : ""
  return `${previous} → ${current} ${unit} (${sign}${change})`
}

/** Read-only client view of their own latest-vs-previous measurements
 * (Measurements V1.1 Module 4). Clients cannot add or edit measurements -
 * only Trainers/Super Admins can (see backend MeasurementService RBAC). */
export function ClientMeasurementsPage() {
  const clientQuery = useQuery({
    queryKey: ["clients", "me"],
    queryFn: clientService.getMe,
  })

  const measurementQuery = useQuery({
    queryKey: ["measurements", "latest", clientQuery.data?.id],
    queryFn: () => measurementService.getLatestMeasurement(clientQuery.data!.id),
    enabled: !!clientQuery.data,
  })

  const isLoading = clientQuery.isLoading || (!!clientQuery.data && measurementQuery.isLoading)

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">My Measurements</h1>
        <p className="text-sm text-muted-foreground">Your latest measurement compared with the one before it.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ruler className="size-4 text-muted-foreground" aria-hidden="true" />
            Latest Measurements
          </CardTitle>
          {measurementQuery.data?.recorded_at && (
            <CardDescription>Recorded {formatDate(measurementQuery.data.recorded_at)}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          )}

          {!clientQuery.isLoading && clientQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(clientQuery.error, "Unable to load your profile.")}
              onRetry={() => clientQuery.refetch()}
            />
          )}

          {!clientQuery.isLoading &&
            !clientQuery.isError &&
            !measurementQuery.isLoading &&
            measurementQuery.isError && (
              <ErrorState
                message={getApiErrorMessage(measurementQuery.error, "Unable to load your measurements.")}
                onRetry={() => measurementQuery.refetch()}
              />
            )}

          {!isLoading && !clientQuery.isError && !measurementQuery.isError && !measurementQuery.data && (
            <EmptyState icon={Ruler} message="No measurements have been recorded for you yet." />
          )}

          {measurementQuery.data && (
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {FIELDS.map((field) => (
                <div key={field.key}>
                  <dt className="text-xs text-muted-foreground">{field.label}</dt>
                  <dd className="text-sm font-medium">
                    {formatMetric(
                      measurementQuery.data![field.key] as number | null,
                      measurementQuery.data![field.previousKey] as number | null,
                      measurementQuery.data![field.changeKey] as number | null,
                      field.unit,
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
