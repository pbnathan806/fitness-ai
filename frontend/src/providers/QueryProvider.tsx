import { useState, type ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            // Was 30s, which meant revisiting any page within that window
            // served cached data with zero network check - including while
            // the backend was completely unreachable, silently. Cached data
            // still paints instantly on mount; this only makes React Query
            // revalidate it over the network every time instead of trusting
            // it blindly for up to 30s.
            staleTime: 0,
          },
        },
      }),
  )

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
