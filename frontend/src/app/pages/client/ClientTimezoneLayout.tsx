import { Outlet } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { clientService } from "@/services/clientService"
import { DisplayTimezoneProvider } from "@/lib/displayTimezone"

/** Wraps every Client-role route so client-facing pages/widgets display
 * times in the client's own profile timezone rather than the browser's -
 * mirrors TrainerTimezoneLayout for the CLIENT role. Shares its query cache
 * key with ClientProfilePage's/ClientPhysicalAssessmentsPage's own getMe()
 * fetch, so this adds no extra network request in the common case. Falls
 * back to undefined (browser-local, formatDateTime/formatDate's existing
 * default) until the profile loads or if the client has no timezone set. */
export function ClientTimezoneLayout() {
  const clientQuery = useQuery({ queryKey: ["clients", "me"], queryFn: clientService.getMe })

  return (
    <DisplayTimezoneProvider timezone={clientQuery.data?.timezone}>
      <Outlet />
    </DisplayTimezoneProvider>
  )
}
