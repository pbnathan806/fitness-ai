import type { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: number
  icon: LucideIcon
  tone?: "default" | "success" | "warning" | "destructive"
  suffix?: string
}

const TONE_CLASSES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "bg-primary/10 text-primary",
  success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  destructive: "bg-destructive/10 text-destructive",
}

export function StatCard({ label, value, icon: Icon, tone = "default", suffix = "" }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3">
        <div className={cn("flex size-10 shrink-0 items-center justify-center rounded-lg", TONE_CLASSES[tone])}>
          <Icon className="size-5" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-2xl font-semibold tabular-nums">
            {value.toLocaleString()}
            {suffix}
          </p>
          <p className="text-xs leading-tight text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex items-center gap-3">
        <Skeleton className="size-10 shrink-0 rounded-lg" />
        <div className="min-w-0 flex-1 space-y-2">
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
      </CardContent>
    </Card>
  )
}
