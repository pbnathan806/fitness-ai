import { useState } from "react"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Pencil, Trash2, CalendarClock, X } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"
import type { TrainerAvailability } from "@/types/trainer"

const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

const slotSchema = z
  .object({
    weekday: z.coerce.number().int().min(0).max(6),
    start_time: z.string().min(1, "Start time is required"),
    end_time: z.string().min(1, "End time is required"),
    is_available: z.enum(["true", "false"]),
  })
  .refine((values) => values.start_time < values.end_time, {
    message: "Start time must be before end time",
    path: ["end_time"],
  })

type SlotFormValues = z.infer<typeof slotSchema>

const DEFAULT_VALUES: SlotFormValues = {
  weekday: 0,
  start_time: "09:00",
  end_time: "10:00",
  is_available: "true",
}

function toTimeInputValue(time: string): string {
  // Backend returns "HH:MM:SS"; the <input type="time"> element wants "HH:MM".
  return time.slice(0, 5)
}

/** Trainer availability page (Task 22.4.1). Full CRUD over
 * `/trainers/me/availability`, scoped to the signed-in trainer. */
export function TrainerAvailabilityPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)

  const availabilityQuery = useQuery({
    queryKey: ["trainers", "me", "availability"],
    queryFn: trainerService.listMyAvailability,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SlotFormValues>({
    resolver: zodResolver(slotSchema) as unknown as Resolver<SlotFormValues>,
    defaultValues: DEFAULT_VALUES,
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["trainers", "me", "availability"] })
  }

  const createMutation = useMutation({
    mutationFn: (values: SlotFormValues) =>
      trainerService.createAvailability({
        weekday: values.weekday,
        start_time: `${values.start_time}:00`,
        end_time: `${values.end_time}:00`,
        is_available: values.is_available === "true",
      }),
    onSuccess: () => {
      invalidate()
      toast.success("Availability slot created.")
      reset(DEFAULT_VALUES)
    },
  })

  const updateMutation = useMutation({
    mutationFn: (values: SlotFormValues) =>
      trainerService.updateAvailability(editingId!, {
        weekday: values.weekday,
        start_time: `${values.start_time}:00`,
        end_time: `${values.end_time}:00`,
        is_available: values.is_available === "true",
      }),
    onSuccess: () => {
      invalidate()
      toast.success("Availability slot updated.")
      setEditingId(null)
      reset(DEFAULT_VALUES)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => trainerService.deleteAvailability(id),
    onSuccess: () => {
      invalidate()
      toast.success("Availability slot deleted.")
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Unable to delete availability slot."))
    },
  })

  const activeMutation = editingId ? updateMutation : createMutation

  function handleEdit(slot: TrainerAvailability) {
    setEditingId(slot.id)
    reset({
      weekday: slot.weekday,
      start_time: toTimeInputValue(slot.start_time),
      end_time: toTimeInputValue(slot.end_time),
      is_available: slot.is_available ? "true" : "false",
    })
  }

  function handleCancelEdit() {
    setEditingId(null)
    reset(DEFAULT_VALUES)
  }

  function handleDelete(slot: TrainerAvailability) {
    const confirmed = window.confirm(
      `Delete the ${WEEKDAY_LABELS[slot.weekday]} ${toTimeInputValue(slot.start_time)}-${toTimeInputValue(slot.end_time)} slot?`,
    )
    if (confirmed) {
      deleteMutation.mutate(slot.id)
    }
  }

  const slots = [...(availabilityQuery.data ?? [])].sort(
    (a, b) => a.weekday - b.weekday || a.start_time.localeCompare(b.start_time),
  )

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Availability</h1>
        <p className="text-sm text-muted-foreground">Manage the weekly time slots when you're available for sessions.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{editingId ? "Edit Slot" : "Add Slot"}</CardTitle>
          <CardDescription>{editingId ? "Update this availability slot." : "Create a new availability slot."}</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((values) => activeMutation.mutate(values))}
            noValidate
            className="space-y-4"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="slot-weekday">Weekday</Label>
                <Select id="slot-weekday" aria-invalid={!!errors.weekday} {...register("weekday")}>
                  {WEEKDAY_LABELS.map((label, index) => (
                    <option key={label} value={index}>
                      {label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="slot-start-time">Start Time</Label>
                <Input id="slot-start-time" type="time" aria-invalid={!!errors.start_time} {...register("start_time")} />
                {errors.start_time && <p className="text-sm text-destructive">{errors.start_time.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="slot-end-time">End Time</Label>
                <Input id="slot-end-time" type="time" aria-invalid={!!errors.end_time} {...register("end_time")} />
                {errors.end_time && <p className="text-sm text-destructive">{errors.end_time.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="slot-is-available">Available</Label>
                <Select id="slot-is-available" {...register("is_available")}>
                  <option value="true">Available</option>
                  <option value="false">Unavailable</option>
                </Select>
              </div>
            </div>

            {activeMutation.isError && (
              <ErrorState title="Couldn't save slot" message={getApiErrorMessage(activeMutation.error)} />
            )}

            <div className="flex gap-2">
              <Button type="submit" disabled={activeMutation.isPending}>
                {activeMutation.isPending ? "Saving..." : editingId ? "Save Changes" : "Add Slot"}
              </Button>
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancelEdit}>
                  <X className="size-4" />
                  Cancel
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Weekly Slots</CardTitle>
        </CardHeader>
        <CardContent>
          {availabilityQuery.isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!availabilityQuery.isLoading && availabilityQuery.isError && (
            <ErrorState message="Unable to load availability." onRetry={() => availabilityQuery.refetch()} />
          )}

          {!availabilityQuery.isLoading && !availabilityQuery.isError && slots.length === 0 && (
            <EmptyState icon={CalendarClock} message="No availability slots yet." />
          )}

          {slots.length > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Weekday</th>
                    <th className="px-3 py-2 font-medium">Start Time</th>
                    <th className="px-3 py-2 font-medium">End Time</th>
                    <th className="px-3 py-2 font-medium">Available</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {slots.map((slot) => (
                    <tr key={slot.id} className="hover:bg-muted/30">
                      <td className="px-3 py-2.5 font-medium">{WEEKDAY_LABELS[slot.weekday]}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">{toTimeInputValue(slot.start_time)}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">{toTimeInputValue(slot.end_time)}</td>
                      <td className="px-3 py-2.5">
                        <Badge variant={slot.is_available ? "success" : "secondary"}>
                          {slot.is_available ? "Available" : "Unavailable"}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon-sm" aria-label="Edit slot" onClick={() => handleEdit(slot)}>
                            <Pencil className="size-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            aria-label="Delete slot"
                            disabled={deleteMutation.isPending}
                            onClick={() => handleDelete(slot)}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
