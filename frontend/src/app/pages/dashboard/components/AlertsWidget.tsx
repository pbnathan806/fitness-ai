import { AlertTriangle, BellRing, CheckCircle2, ClipboardX, UserX } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { cn } from "@/lib/utils"
import type { SuperAdminDashboardStats } from "@/types/dashboard"

interface AlertsWidgetProps {
  stats: SuperAdminDashboardStats | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

interface AlertEntry {
  id: string
  icon: LucideIcon
  message: string
  tone: "destructive" | "warning"
}

/** Derived from the same super-admin stats payload - no separate alerts API
 * exists, so thresholds already crossed in the aggregate counts become
 * simple rule-based alerts. */
function buildAlerts(stats: SuperAdminDashboardStats): AlertEntry[] {
  const alerts: AlertEntry[] = []

  if (stats.clients_missing_check_ins_today > 0) {
    alerts.push({
      id: "missing-check-ins",
      icon: ClipboardX,
      message: `${stats.clients_missing_check_ins_today} client${stats.clients_missing_check_ins_today === 1 ? "" : "s"} missing today's check-in`,
      tone: "warning",
    })
  }

  if (stats.expired_clients > 0) {
    alerts.push({
      id: "expired-clients",
      icon: AlertTriangle,
      message: `${stats.expired_clients} client${stats.expired_clients === 1 ? "" : "s"} with expired subscriptions`,
      tone: "destructive",
    })
  }

  if (stats.inactive_clients > 0) {
    alerts.push({
      id: "inactive-clients",
      icon: UserX,
      message: `${stats.inactive_clients} client${stats.inactive_clients === 1 ? "" : "s"} with no active subscription`,
      tone: "warning",
    })
  }

  return alerts
}

const TONE_CLASSES: Record<AlertEntry["tone"], string> = {
  destructive: "text-destructive",
  warning: "text-amber-600 dark:text-amber-400",
}

export function AlertsWidget({ stats, isLoading, isError, onRetry }: AlertsWidgetProps) {
  const alerts = stats ? buildAlerts(stats) : []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BellRing className="size-4 text-muted-foreground" aria-hidden="true" />
          Alerts
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isLoading && isError && <ErrorState message="Couldn't load alerts." onRetry={onRetry} />}

        {!isLoading && !isError && alerts.length === 0 && (
          <p className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            No alerts. Everything looks good.
          </p>
        )}

        {!isLoading && !isError && alerts.length > 0 && (
          <ul className="divide-y">
            {alerts.map((alert) => (
              <li key={alert.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                <alert.icon className={cn("size-4 shrink-0", TONE_CLASSES[alert.tone])} aria-hidden="true" />
                <p className="text-sm">{alert.message}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
