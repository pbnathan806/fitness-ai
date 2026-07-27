import { User } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SUPPORTED_TIMEZONES } from "@/lib/constants"
import type { Client } from "@/types/client"

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  )
}

/** Client profile summary (Task 22.3). Date of Birth, Gender, Emergency
 * Contact, and an Active/Inactive status are part of the original spec but
 * have no backing fields on the backend's Client model - they are omitted
 * here rather than shown as dead UI. See the task's "Known limitations". */
export function ClientDetailsCard({ client }: { client: Client }) {
  const timezoneLabel = SUPPORTED_TIMEZONES.find((tz) => tz.value === client.timezone)?.label ?? client.timezone

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="size-4 text-muted-foreground" aria-hidden="true" />
          Profile
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" value={`${client.first_name} ${client.last_name}`} />
        <Field label="Email" value={client.email} />
        <Field label="Phone" value={client.phone_number ?? "Not provided"} />
        <Field label="Timezone" value={timezoneLabel} />
      </CardContent>
    </Card>
  )
}
