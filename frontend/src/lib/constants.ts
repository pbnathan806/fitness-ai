export const Role = {
  SUPER_ADMIN: "SUPER_ADMIN",
  TRAINER: "TRAINER",
  CLIENT: "CLIENT",
} as const

export type RoleName = (typeof Role)[keyof typeof Role]

export const ALL_ROLES: RoleName[] = [Role.SUPER_ADMIN, Role.TRAINER, Role.CLIENT]

export const ROLE_LABELS: Record<RoleName, string> = {
  [Role.SUPER_ADMIN]: "Super Admin",
  [Role.TRAINER]: "Trainer",
  [Role.CLIENT]: "Client",
}

export const ROLE_HOME_PATH: Record<RoleName, string> = {
  [Role.SUPER_ADMIN]: "/super-admin/dashboard",
  [Role.TRAINER]: "/trainer/dashboard",
  [Role.CLIENT]: "/client/dashboard",
}

export const ROLE_CHANGE_PASSWORD_PATH: Record<RoleName, string> = {
  [Role.SUPER_ADMIN]: "/super-admin/change-password",
  [Role.TRAINER]: "/trainer/change-password",
  [Role.CLIENT]: "/client/change-password",
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1"

export const AUTH_STORAGE_KEY = "fitness_ai.auth"

/** IANA identifiers for the timezones this platform supports (US + IST, per
 * TIMEZONE_REQUIREMENTS.md). Kept to a curated list so client/trainer forms
 * offer a picker instead of free-text timezone entry. */
export const SUPPORTED_TIMEZONES: { value: string; label: string }[] = [
  { value: "America/New_York", label: "Eastern Time (US)" },
  { value: "America/Chicago", label: "Central Time (US)" },
  { value: "America/Denver", label: "Mountain Time (US)" },
  { value: "America/Los_Angeles", label: "Pacific Time (US)" },
  { value: "Asia/Kolkata", label: "India Standard Time (IST)" },
]
