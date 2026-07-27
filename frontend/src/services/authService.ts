import { apiClient } from "@/services/apiClient"
import type { LoginRequest, LoginResponse, SwitchRoleResponse } from "@/types/auth"
import type { RoleName } from "@/lib/constants"

export const authService = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>("/auth/login", payload)
    return data
  },

  async switchRole(role: RoleName): Promise<SwitchRoleResponse> {
    const { data } = await apiClient.post<SwitchRoleResponse>("/auth/switch-role", { role })
    return data
  },
}
