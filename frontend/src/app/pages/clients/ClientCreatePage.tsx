import { useNavigate, Link } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ChevronLeft } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ClientForm, type ClientFormValues } from "@/app/pages/clients/components/ClientForm"
import { clientService } from "@/services/clientService"
import { getApiErrorMessage } from "@/lib/errors"

export function ClientCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (values: ClientFormValues) =>
      clientService.createClient({
        email: values.email,
        password: values.password,
        first_name: values.first_name,
        last_name: values.last_name,
        phone_number: values.phone_number || null,
        timezone: values.timezone,
      }),
    onSuccess: () => {
      // Without this the list page's cached ["clients", "all"] (staleTime 30s)
      // wouldn't include the new client until the cache expired or a refresh.
      queryClient.invalidateQueries({ queryKey: ["clients", "all"] })
      toast.success("Client created successfully.")
      navigate("/super-admin/clients")
    },
  })

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" render={<Link to="/super-admin/clients" />} nativeButton={false}>
        <ChevronLeft className="size-4" />
        Back to clients
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>New Client</CardTitle>
          <CardDescription>Create a client profile. The client can then be assigned to trainers.</CardDescription>
        </CardHeader>
        <CardContent>
          <ClientForm
            mode="create"
            defaultValues={{ timezone: "" }}
            onSubmit={(values) => createMutation.mutate(values)}
            isSubmitting={createMutation.isPending}
            submitErrorMessage={createMutation.isError ? getApiErrorMessage(createMutation.error) : null}
            submitLabel="Create Client"
          />
        </CardContent>
      </Card>
    </div>
  )
}
