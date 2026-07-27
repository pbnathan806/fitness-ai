import { Construction } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface PlaceholderPageProps {
  title: string
}

/** Stands in for a not-yet-built business screen. Task-22.1 is frontend
 * foundation only — the nav destinations exist so RBAC/layout can be
 * exercised end-to-end, without pulling business features into scope. */
export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Construction className="size-5 text-muted-foreground" aria-hidden="true" />
          {title}
        </CardTitle>
        <CardDescription>This screen will be implemented in a future task.</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">Coming soon.</CardContent>
    </Card>
  )
}
