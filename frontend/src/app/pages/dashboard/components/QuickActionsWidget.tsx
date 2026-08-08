import { Link } from "react-router-dom"
import { Users, UserCog, CreditCard, CalendarDays, type LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export interface QuickAction {
  label: string
  path: string
  icon: LucideIcon
}

const SUPER_ADMIN_QUICK_ACTIONS: QuickAction[] = [
  { label: "Manage Clients", path: "/super-admin/clients", icon: Users },
  { label: "Manage Trainers", path: "/super-admin/trainers", icon: UserCog },
  { label: "Subscriptions", path: "/super-admin/subscriptions", icon: CreditCard },
  { label: "Sessions", path: "/super-admin/sessions", icon: CalendarDays },
]

interface QuickActionsWidgetProps {
  /** Defaults to the Super Admin shortcut set so the existing Super Admin
   * dashboard usage renders unchanged. */
  actions?: QuickAction[]
}

export function QuickActionsWidget({ actions = SUPER_ADMIN_QUICK_ACTIONS }: QuickActionsWidgetProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {actions.map((action) => (
            <Link
              key={action.path}
              to={action.path}
              className="flex flex-col items-center gap-1.5 rounded-lg border px-3 py-3 text-center text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <action.icon className="size-5" aria-hidden="true" />
              {action.label}
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
