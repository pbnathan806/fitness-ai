import { useNavigate, useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { SessionEditForm } from "@/app/pages/sessions/components/SessionEditForm"
import { sessionService } from "@/services/sessionService"
import { getApiErrorMessage } from "@/lib/errors"
import type { SessionUpdateInput } from "@/types/session"

export function SessionEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const sessionQuery = useQuery({
    queryKey: ["sessions", id],
    queryFn: () => sessionService.getSession(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (values: SessionUpdateInput) => sessionService.updateSession(id!, values),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sessions", id], updated)
      queryClient.invalidateQueries({ queryKey: ["sessions", "all"] })
      toast.success("Session updated successfully.")
      navigate(`/super-admin/sessions/${id}`)
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to={`/super-admin/sessions/${id}`} />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to session
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Edit Session</CardTitle>
          <CardDescription>Update the scheduled start, meeting type, meeting link, or status.</CardDescription>
        </CardHeader>
        <CardContent>
          {sessionQuery.isLoading && <LoadingSpinner label="Loading session..." className="py-8" />}

          {sessionQuery.isError && (
            <ErrorState
              message={getApiErrorMessage(sessionQuery.error, "This session could not be found.")}
              onRetry={() => sessionQuery.refetch()}
            />
          )}

          {sessionQuery.data && (
            <SessionEditForm
              session={sessionQuery.data}
              onSubmit={(values) => updateMutation.mutate(values)}
              isSubmitting={updateMutation.isPending}
              submitErrorMessage={updateMutation.isError ? getApiErrorMessage(updateMutation.error) : null}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
