import { apiClient } from "@/services/apiClient"
import type {
  ChangePasswordResponse,
  ForgotPasswordResponse,
  LoginRequest,
  LoginResponse,
  ResetPasswordResponse,
  SwitchRoleResponse,
} from "@/types/auth"
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

  /** Always returns the same generic message regardless of whether the email
   * is registered (anti-enumeration, enforced server-side) - callers should
   * show it as-is rather than branching on success/failure. */
  async forgotPassword(email: string): Promise<ForgotPasswordResponse> {
    const { data } = await apiClient.post<ForgotPasswordResponse>("/auth/forgot-password", { email })
    return data
  },

  async resetPassword(token: string, newPassword: string): Promise<ResetPasswordResponse> {
    const { data } = await apiClient.post<ResetPasswordResponse>("/auth/reset-password", {
      token,
      new_password: newPassword,
    })
    return data
  },

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<ChangePasswordResponse> {
    const { data } = await apiClient.post<ChangePasswordResponse>("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return data
  },
}
