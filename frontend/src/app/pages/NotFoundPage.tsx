import { Link } from "react-router-dom"
import { Compass } from "lucide-react"
import { Button } from "@/components/ui/button"

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center gap-4 p-8 text-center">
      <Compass className="size-10 text-muted-foreground" aria-hidden="true" />
      <h1 className="text-xl font-semibold">Page not found</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        The page you're looking for doesn't exist or has moved.
      </p>
      <Button render={<Link to="/" />} nativeButton={false}>
        Back to dashboard
      </Button>
    </div>
  )
}
