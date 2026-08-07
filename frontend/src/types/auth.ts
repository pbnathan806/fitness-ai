import type { RoleName } from "@/lib/constants"

export interface LoginRequest {
  email: string
  password: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ForgotPasswordResponse {
  message: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface ResetPasswordResponse {
  message: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface ChangePasswordResponse {
  message: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: string
  roles: RoleName[]
}

export interface SwitchRoleResponse {
  access_token: string
  token_type: string
  expires_in: number
  active_role: RoleName
  roles: RoleName[]
}

/** Persisted client-side session. `access_token` always carries `active_role`
 * once a role has been selected via `/auth/switch-role`. */
export interface AuthSession {
  accessToken: string
  tokenType: string
  expiresAt: number
  userId: string
  roles: RoleName[]
  activeRole: RoleName | null
}
