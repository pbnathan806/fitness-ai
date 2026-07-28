import { User } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SUPPORTED_TIMEZONES } from "@/lib/constants"
import type { Trainer } from "@/types/trainer"

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  )
}

/** Trainer profile summary for the Details page (Task 22.4.1), backed by
 * the real `GET /trainers/{id}` endpoint. */
export function TrainerDetailsCard({ trainer }: { trainer: Trainer }) {
  const timezoneLabel = SUPPORTED_TIMEZONES.find((tz) => tz.value === trainer.timezone)?.label ?? trainer.timezone ?? "Not set"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="size-4 text-muted-foreground" aria-hidden="true" />
          Profile
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" value={`${trainer.first_name} ${trainer.last_name}`} />
        <Field label="Email" value={trainer.email} />
        <Field label="Phone" value={trainer.phone_number ?? "Not provided"} />
        <Field label="Timezone" value={timezoneLabel} />
        <div>
          <p className="text-xs text-muted-foreground">Status</p>
          <Badge variant={trainer.is_active ? "success" : "secondary"} className="mt-0.5">
            {trainer.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
