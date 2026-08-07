import { Menu, LogOut, ChevronDown, KeyRound } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/hooks/useAuth"
import { ROLE_CHANGE_PASSWORD_PATH, ROLE_HOME_PATH, ROLE_LABELS, type RoleName } from "@/lib/constants"

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { session, selectRole, logout } = useAuth()
  const navigate = useNavigate()
  if (!session?.activeRole) return null

  const activeRole = session.activeRole
  const otherRoles = session.roles.filter((role) => role !== activeRole)

  const handleSwitchRole = (role: RoleName) => {
    selectRole(role).then(() => navigate(ROLE_HOME_PATH[role]))
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuClick} aria-label="Open menu">
          <Menu className="size-5" />
        </Button>
        <h1 className="text-sm font-medium text-muted-foreground sm:text-base">
          {ROLE_LABELS[session.activeRole]} Dashboard
        </h1>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2 py-1.5 outline-none hover:bg-muted">
          <Avatar className="size-8">
            <AvatarFallback>{session.activeRole.charAt(0)}</AvatarFallback>
          </Avatar>
          <ChevronDown className="size-4 text-muted-foreground" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuGroup>
            <DropdownMenuLabel>{ROLE_LABELS[session.activeRole]}</DropdownMenuLabel>
          </DropdownMenuGroup>
          {otherRoles.length > 0 && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                  Switch role
                </DropdownMenuLabel>
                {otherRoles.map((role: RoleName) => (
                  <DropdownMenuItem key={role} onClick={() => handleSwitchRole(role)}>
                    {ROLE_LABELS[role]}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuGroup>
            </>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem onClick={() => navigate(ROLE_CHANGE_PASSWORD_PATH[activeRole])}>
              <KeyRound className="size-4" />
              Change Password
            </DropdownMenuItem>
            <DropdownMenuItem onClick={logout} variant="destructive">
              <LogOut className="size-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
