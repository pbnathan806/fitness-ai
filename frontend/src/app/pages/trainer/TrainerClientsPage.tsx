import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Users, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/common/ErrorState"
import { EmptyState } from "@/components/common/EmptyState"
import { assignmentService } from "@/services/assignmentService"

/** Trainer's own assigned-clients roster, via GET /assignments/my-clients
 * (TRAINER-only; scoping is already enforced server-side, see
 * AssignmentService.list_my_clients). Read-only - no assign/remove actions
 * here, those remain SUPER_ADMIN-only via TrainerAssignmentCard. */
export function TrainerClientsPage() {
  const clientsQuery = useQuery({
    queryKey: ["assignments", "my-clients"],
    queryFn: assignmentService.getMyClients,
  })

  const clients = clientsQuery.data ?? []

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Assigned Clients</h1>
        <p className="text-sm text-muted-foreground">Clients currently assigned to you.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <Users className="size-4 text-muted-foreground" aria-hidden="true" />
              Assigned Clients
            </CardTitle>
            {!clientsQuery.isLoading && !clientsQuery.isError && (
              <Badge variant="secondary">{clients.length} assigned</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {clientsQuery.isLoading && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">Loading assigned clients...</p>
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!clientsQuery.isLoading && clientsQuery.isError && (
            <ErrorState
              title="Unable to load assigned clients."
              message="Please try again."
              onRetry={() => clientsQuery.refetch()}
            />
          )}

          {!clientsQuery.isLoading && !clientsQuery.isError && clients.length === 0 && (
            <EmptyState icon={Users} message="You do not have any assigned clients." />
          )}

          {!clientsQuery.isLoading && !clientsQuery.isError && clients.length > 0 && (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Client Name</th>
                    <th className="px-3 py-2 font-medium">Email</th>
                    <th className="px-3 py-2 font-medium">Phone Number</th>
                    <th className="px-3 py-2 font-medium">Timezone</th>
                    <th className="px-3 py-2 font-medium">Primary</th>
                    <th className="px-3 py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {clients.map((client) => (
                    <tr key={client.assignment_id} className="hover:bg-muted/30">
                      <td className="max-w-[200px] truncate px-3 py-2.5 font-medium">
                        {client.first_name} {client.last_name}
                      </td>
                      <td className="max-w-[220px] truncate px-3 py-2.5 text-muted-foreground">{client.email}</td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                        {client.phone_number ?? "—"}
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">{client.timezone}</td>
                      <td className="px-3 py-2.5">
                        <Badge variant={client.is_primary ? "default" : "secondary"}>
                          {client.is_primary ? "Yes" : "No"}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          render={<Link to={`/trainer/clients/${client.client_id}`} />}
                          nativeButton={false}
                        >
                          <Eye className="size-4" />
                          View Client
                        </Button>
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
