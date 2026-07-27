import { NavLink } from "react-router-dom"
import { Dumbbell, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { NAV_ITEMS } from "@/lib/navigation"
import { ROLE_LABELS, type RoleName } from "@/lib/constants"
import { Button } from "@/components/ui/button"

interface SidebarProps {
  activeRole: RoleName
  open: boolean
  onClose: () => void
}

function SidebarContent({ activeRole, onNavigate }: { activeRole: RoleName; onNavigate?: () => void }) {
  const items = NAV_ITEMS[activeRole]

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-5">
        <Dumbbell className="size-6 text-primary" aria-hidden="true" />
        <span className="text-lg font-semibold">Fitness AI</span>
      </div>
      <nav className="flex-1 space-y-1 px-2" aria-label={`${ROLE_LABELS[activeRole]} navigation`}>
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <item.icon className="size-4" aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t px-4 py-3 text-xs text-muted-foreground">{ROLE_LABELS[activeRole]}</div>
    </div>
  )
}

export function Sidebar({ activeRole, open, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop */}
      <aside className="hidden w-64 shrink-0 border-r bg-card md:flex">
        <SidebarContent activeRole={activeRole} />
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
          <div className="absolute inset-y-0 left-0 w-64 bg-card shadow-lg">
            <div className="flex justify-end p-2">
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close menu">
                <X className="size-5" />
              </Button>
            </div>
            <SidebarContent activeRole={activeRole} onNavigate={onClose} />
          </div>
        </div>
      )}
    </>
  )
}
