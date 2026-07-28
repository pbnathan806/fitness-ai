import { apiClient } from "@/services/apiClient"
import type { ApplicationSetting, ApplicationSettingUpdateInput } from "@/types/applicationSetting"

export const applicationSettingService = {
  async listSettings(): Promise<ApplicationSetting[]> {
    const { data } = await apiClient.get<ApplicationSetting[]>("/application-settings")
    return data
  },

  async getSetting(key: string): Promise<ApplicationSetting> {
    const { data } = await apiClient.get<ApplicationSetting>(`/application-settings/${key}`)
    return data
  },

  async updateSetting(key: string, payload: ApplicationSettingUpdateInput): Promise<ApplicationSetting> {
    const { data } = await apiClient.patch<ApplicationSetting>(`/application-settings/${key}`, payload)
    return data
  },
}
