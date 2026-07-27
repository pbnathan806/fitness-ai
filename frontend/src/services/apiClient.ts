import axios from "axios"
import { API_BASE_URL } from "@/lib/constants"
import { clearStoredSession, readStoredSession } from "@/lib/storage"

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.request.use((config) => {
  const session = readStoredSession()
  if (session?.accessToken) {
    config.headers.Authorization = `${session.tokenType ?? "Bearer"} ${session.accessToken}`
  }
  return config
})

type UnauthorizedHandler = () => void

let unauthorizedHandler: UnauthorizedHandler | null = null

/** Registered by `AuthProvider` so a 401 from any request can clear the
 * session and redirect to `/login`, without the client importing React Router. */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const requestUrl: string = error?.config?.url ?? ""
    const isLoginRequest = requestUrl.includes("/auth/login")

    if (status === 401 && !isLoginRequest) {
      clearStoredSession()
      unauthorizedHandler?.()
    }

    return Promise.reject(error)
  },
)
