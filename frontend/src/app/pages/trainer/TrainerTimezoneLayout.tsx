import { Outlet } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { trainerService } from "@/services/trainerService"
import { DisplayTimezoneProvider } from "@/lib/displayTimezone"

/** Wraps every Trainer-role route so trainer-facing pages/widgets display
 * times in the trainer's own profile timezone rather than the browser's -
 * see memory project_deferred_trainer_timezone_framing. Shares its query
 * cache key with TrainerProfilePage's own getSelf() fetch, so this adds no
 * extra network request in the common case. Falls back to undefined
 * (browser-local, formatDateTime/formatDate's existing default) until the
 * profile loads or if the trainer has no timezone set. */
export function TrainerTimezoneLayout() {
  const trainerQuery = useQuery({ queryKey: ["trainers", "me"], queryFn: trainerService.getSelf })

  return (
    <DisplayTimezoneProvider timezone={trainerQuery.data?.timezone ?? undefined}>
      <Outlet />
    </DisplayTimezoneProvider>
  )
}
