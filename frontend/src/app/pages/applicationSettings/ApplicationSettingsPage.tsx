import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Pencil, Settings, X } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { applicationSettingService } from "@/services/applicationSettingService"
import { getApiErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"

/** Minimal SUPER_ADMIN screen over the existing generic application-settings
 * key/value API (Task-20 backend, no frontend until now) - one row per
 * setting, inline value editing. New settings are seeded via backend
 * migrations, not created here (the API has no create endpoint). */
export function ApplicationSettingsPage() {
  const queryClient = useQueryClient()
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")

  const settingsQuery = useQuery({
    queryKey: ["application-settings"],
    queryFn: applicationSettingService.listSettings,
  })

  const updateMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      applicationSettingService.updateSetting(key, { value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["application-settings"] })
      toast.success("Setting updated successfully.")
      setEditingKey(null)
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to update setting."))
    },
  })

  function startEdit(key: string, value: string) {
    setEditingKey(key)
    setEditValue(value)
  }

  function cancelEdit() {
    setEditingKey(null)
    setEditValue("")
  }

  function saveEdit(key: string) {
    if (!editValue.trim()) return
    updateMutation.mutate({ key, value: editValue.trim() })
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Application Settings</h1>
        <p className="text-sm text-muted-foreground">Configure operational values used across the platform.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="size-4 text-muted-foreground" aria-hidden="true" />
            Settings
          </CardTitle>
          <CardDescription>Changes take effect immediately.</CardDescription>
        </CardHeader>
        <CardContent>
          {settingsQuery.isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          )}

          {!settingsQuery.isLoading && settingsQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(settingsQuery.error, "Unable to load application settings.")}
              onRetry={() => settingsQuery.refetch()}
            />
          )}

          {!settingsQuery.isLoading && !settingsQuery.isError && (settingsQuery.data?.length ?? 0) === 0 && (
            <EmptyState icon={Settings} message="No application settings found." />
          )}

          {(settingsQuery.data?.length ?? 0) > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Key</th>
                    <th className="px-3 py-2 font-medium">Description</th>
                    <th className="px-3 py-2 font-medium">Value</th>
                    <th className="px-3 py-2 font-medium">Updated</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {settingsQuery.data!.map((setting) => {
                    const isEditing = editingKey === setting.key
                    const isSaving = updateMutation.isPending && updateMutation.variables?.key === setting.key

                    return (
                      <tr key={setting.key} className="hover:bg-muted/30">
                        <td className="px-3 py-2.5 font-medium whitespace-nowrap">{setting.key}</td>
                        <td className="max-w-[320px] px-3 py-2.5 text-muted-foreground">{setting.description ?? "—"}</td>
                        <td className="px-3 py-2.5">
                          {isEditing ? (
                            <Input
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              disabled={isSaving}
                              className="max-w-xs"
                              autoFocus
                            />
                          ) : (
                            <span className="font-mono text-xs">{setting.value}</span>
                          )}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                          {formatDateTime(setting.updated_at)}
                        </td>
                        <td className="px-3 py-2.5 text-right whitespace-nowrap">
                          {isEditing ? (
                            <div className="flex justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                aria-label="Save"
                                disabled={isSaving}
                                onClick={() => saveEdit(setting.key)}
                              >
                                <Check className="size-4" />
                              </Button>
                              <Button variant="ghost" size="icon-sm" aria-label="Cancel" disabled={isSaving} onClick={cancelEdit}>
                                <X className="size-4" />
                              </Button>
                            </div>
                          ) : (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              aria-label="Edit setting"
                              onClick={() => startEdit(setting.key, setting.value)}
                            >
                              <Pencil className="size-4" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
