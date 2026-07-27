import { Link } from "react-router-dom"
import { Users, UserCog, CreditCard, CalendarDays, type LucideIcon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface QuickAction {
  label: string
  path: string
  icon: LucideIcon
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: "Manage Clients", path: "/super-admin/clients", icon: Users },
  { label: "Manage Trainers", path: "/super-admin/trainers", icon: UserCog },
  { label: "Subscriptions", path: "/super-admin/subscriptions", icon: CreditCard },
  { label: "Sessions", path: "/super-admin/sessions", icon: CalendarDays },
]

export function QuickActionsWidget() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((action) => (
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
