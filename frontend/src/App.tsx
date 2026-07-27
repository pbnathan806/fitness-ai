import { RouterProvider } from "react-router-dom"
import { Toaster } from "@/components/ui/sonner"
import { QueryProvider } from "@/providers/QueryProvider"
import { AuthProvider } from "@/providers/AuthProvider"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { router } from "@/app/routes"

function App() {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <AuthProvider>
          <RouterProvider router={router} />
          <Toaster position="top-right" />
        </AuthProvider>
      </QueryProvider>
    </ErrorBoundary>
  )
}

export default App
