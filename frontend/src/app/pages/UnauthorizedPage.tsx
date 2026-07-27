import { Link } from "react-router-dom"
import { ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center gap-4 p-8 text-center">
      <ShieldAlert className="size-10 text-destructive" aria-hidden="true" />
      <h1 className="text-xl font-semibold">You don't have access to this page</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Your current role doesn't include permission to view this section.
      </p>
      <Button render={<Link to="/" />} nativeButton={false}>
        Back to dashboard
      </Button>
    </div>
  )
}
