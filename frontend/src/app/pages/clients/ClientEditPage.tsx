import { useNavigate, useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { ErrorState } from "@/components/common/ErrorState"
import { ClientForm, type ClientFormValues } from "@/app/pages/clients/components/ClientForm"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"

export function ClientEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const clientQuery = useQuery({
    queryKey: ["clients", id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (values: ClientFormValues) =>
      clientService.updateClient(id!, {
        first_name: values.first_name,
        last_name: values.last_name,
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: (updatedClient) => {
      // The details page reads the same ["clients", id] cache entry - without
      // this it kept showing the pre-edit data (e.g. old timezone) until the
      // 30s staleTime elapsed or the user hard-refreshed.
      queryClient.setQueryData(["clients", id], updatedClient)
      queryClient.invalidateQueries({ queryKey: ["clients", "all"] })
      toast.success("Client updated successfully.")
      navigate(`/super-admin/clients/${id}`)
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to={`/super-admin/clients/${id}`} />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to client
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Edit Client</CardTitle>
          <CardDescription>
            {clientQuery.data ? `${clientQuery.data.first_name} ${clientQuery.data.last_name}` : "Update client details."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {clientQuery.isLoading && <LoadingSpinner label="Loading client details..." className="py-8" />}

          {clientQuery.isError && (
            <ErrorState message={getApiErrorMessage(clientQuery.error)} onRetry={() => clientQuery.refetch()} />
          )}

          {clientQuery.data && (
            <ClientForm
              mode="edit"
              defaultValues={{
                first_name: clientQuery.data.first_name,
                last_name: clientQuery.data.last_name,
                phone_number: clientQuery.data.phone_number ?? "",
                timezone: clientQuery.data.timezone,
              }}
              onSubmit={(values) => updateMutation.mutate(values)}
              isSubmitting={updateMutation.isPending}
              submitErrorMessage={updateMutation.isError ? getApiErrorMessage(updateMutation.error) : null}
              submitLabel="Save Changes"
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
