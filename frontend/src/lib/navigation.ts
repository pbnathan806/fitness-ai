import {
  LayoutDashboard,
  Users,
  UserCog,
  CreditCard,
  CalendarDays,
  ClipboardList,
  ClipboardCheck,
  BarChart3,
  Bell,
  UserCircle,
  TrendingUp,
  type LucideIcon,
} from "lucide-react"
import { Role, type RoleName } from "@/lib/constants"

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
}

/** Nav structure only — the linked pages beyond Dashboard are placeholders.
 * Business screens are out of scope for this task (frontend foundation only). */
export const NAV_ITEMS: Record<RoleName, NavItem[]> = {
  [Role.SUPER_ADMIN]: [
    { label: "Dashboard", path: "/super-admin/dashboard", icon: LayoutDashboard },
    { label: "Clients", path: "/super-admin/clients", icon: Users },
    { label: "Trainers", path: "/super-admin/trainers", icon: UserCog },
    { label: "Subscriptions", path: "/super-admin/subscriptions", icon: CreditCard },
    { label: "Sessions", path: "/super-admin/sessions", icon: CalendarDays },
    { label: "Reports", path: "/super-admin/reports", icon: BarChart3 },
    { label: "Notifications", path: "/super-admin/notifications", icon: Bell },
  ],
  [Role.TRAINER]: [
    { label: "Dashboard", path: "/trainer/dashboard", icon: LayoutDashboard },
    { label: "Assigned Clients", path: "/trainer/clients", icon: Users },
    { label: "Sessions", path: "/trainer/sessions", icon: CalendarDays },
    { label: "Session Notes", path: "/trainer/session-notes", icon: ClipboardList },
    { label: "Check-ins", path: "/trainer/check-ins", icon: ClipboardCheck },
    { label: "Reports", path: "/trainer/reports", icon: BarChart3 },
  ],
  [Role.CLIENT]: [
    { label: "Dashboard", path: "/client/dashboard", icon: LayoutDashboard },
    { label: "Profile", path: "/client/profile", icon: UserCircle },
    { label: "Progress", path: "/client/progress", icon: TrendingUp },
    { label: "Check-ins", path: "/client/check-ins", icon: ClipboardCheck },
    { label: "Reports", path: "/client/reports", icon: BarChart3 },
    { label: "Notifications", path: "/client/notifications", icon: Bell },
  ],
}
