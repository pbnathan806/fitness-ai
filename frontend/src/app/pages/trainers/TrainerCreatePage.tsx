import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft, KeyRound } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { TrainerForm, type TrainerFormValues } from "@/app/pages/trainers/components/TrainerForm"
import { trainerService } from "@/services/trainerService"
import { getApiErrorMessage } from "@/lib/errors"

export function TrainerCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (values: TrainerFormValues) =>
      trainerService.createTrainer({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["trainers"] })
      toast.success("Trainer created successfully.")
      setTemporaryPassword(created.temporary_password)
    },
  })

  if (temporaryPassword) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Trainer Created</CardTitle>
            <CardDescription>Share this temporary password with the trainer so they can sign in.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <KeyRound />
              <AlertTitle>Temporary password</AlertTitle>
              <AlertDescription>
                <p className="font-mono text-sm select-all">{temporaryPassword}</p>
                <p className="mt-1">
                  This password is only shown once. The trainer should change it after their first sign-in.
                </p>
              </AlertDescription>
            </Alert>
            <Button onClick={() => navigate("/super-admin/trainers")}>Continue to Trainers</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/trainers" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to trainers
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>New Trainer</CardTitle>
          <CardDescription>Create a trainer profile. A temporary password will be generated.</CardDescription>
        </CardHeader>
        <CardContent>
          <TrainerForm
            mode="create"
            defaultValues={{ timezone: "" }}
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Create Trainer"
          />
        </CardContent>
      </Card>
    </div>
  )
}
