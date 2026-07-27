import { useState } from "react"
import { Outlet } from "react-router-dom"
import { Sidebar } from "@/components/layout/Sidebar"
import { Header } from "@/components/layout/Header"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { useAuth } from "@/hooks/useAuth"
import { FullPageSpinner } from "@/components/common/LoadingSpinner"

export function AppLayout() {
  const { session } = useAuth()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  if (!session?.activeRole) {
    return <FullPageSpinner />
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar activeRole={session.activeRole} open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
