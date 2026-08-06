import {
  LayoutDashboard,
  Users,
  UserCog,
  CreditCard,
  Package,
  CalendarDays,
  CalendarClock,
  ClipboardList,
  ClipboardCheck,
  Ruler,
  BarChart3,
  Bell,
  UserCircle,
  TrendingUp,
  Settings,
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
    { label: "Subscription Plans", path: "/super-admin/subscription-plans", icon: Package },
    { label: "Subscriptions", path: "/super-admin/subscriptions", icon: CreditCard },
    { label: "Sessions", path: "/super-admin/sessions", icon: CalendarDays },
    { label: "Check-ins", path: "/super-admin/check-ins", icon: ClipboardCheck },
    { label: "Measurements", path: "/super-admin/measurements", icon: Ruler },
    { label: "Reports", path: "/super-admin/reports", icon: BarChart3 },
    { label: "Notifications", path: "/super-admin/notifications", icon: Bell },
    { label: "Settings", path: "/super-admin/settings", icon: Settings },
  ],
  [Role.TRAINER]: [
    { label: "Dashboard", path: "/trainer/dashboard", icon: LayoutDashboard },
    { label: "Assigned Clients", path: "/trainer/clients", icon: Users },
    { label: "Sessions", path: "/trainer/sessions", icon: CalendarDays },
    { label: "Session Notes", path: "/trainer/session-notes", icon: ClipboardList },
    { label: "Check-ins", path: "/trainer/check-ins", icon: ClipboardCheck },
    { label: "Measurements", path: "/trainer/measurements", icon: Ruler },
    { label: "Availability", path: "/trainer/availability", icon: CalendarClock },
    { label: "Reports", path: "/trainer/reports", icon: BarChart3 },
    { label: "Profile", path: "/trainer/profile", icon: UserCircle },
  ],
  [Role.CLIENT]: [
    { label: "Dashboard", path: "/client/dashboard", icon: LayoutDashboard },
    { label: "Profile", path: "/client/profile", icon: UserCircle },
    { label: "Subscriptions", path: "/client/subscriptions", icon: CreditCard },
    { label: "My Sessions", path: "/client/my-sessions", icon: CalendarDays },
    { label: "Progress", path: "/client/progress", icon: TrendingUp },
    { label: "Check-ins", path: "/client/check-ins", icon: ClipboardCheck },
    { label: "Measurements", path: "/client/measurements", icon: Ruler },
    { label: "Reports", path: "/client/reports", icon: BarChart3 },
    { label: "Notifications", path: "/client/notifications", icon: Bell },
  ],
}
