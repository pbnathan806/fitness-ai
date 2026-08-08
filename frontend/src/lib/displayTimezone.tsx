import { createContext, useContext, type ReactNode } from "react"

/** Timezone that trainer-facing time displays should render in, instead of
 * the browser's local timezone. `undefined` outside a DisplayTimezoneProvider
 * (Super Admin and Client keep formatDateTime/formatDate's default
 * browser-local behavior unchanged - only the Trainer route tree provides a
 * real value here). See memory project_deferred_trainer_timezone_framing. */
const DisplayTimezoneContext = createContext<string | undefined>(undefined)

export function DisplayTimezoneProvider({
  timezone,
  children,
}: {
  timezone: string | undefined
  children: ReactNode
}) {
  return (
    <DisplayTimezoneContext.Provider value={timezone}>{children}</DisplayTimezoneContext.Provider>
  )
}

export function useDisplayTimezone(): string | undefined {
  return useContext(DisplayTimezoneContext)
}
