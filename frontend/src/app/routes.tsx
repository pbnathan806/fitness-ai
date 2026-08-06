import { Navigate, createBrowserRouter, type RouteObject } from "react-router-dom"
import { ProtectedRoute } from "@/components/common/ProtectedRoute"
import { AppLayout } from "@/components/layout/AppLayout"
import { LoginPage } from "@/app/pages/LoginPage"
import { ForgotPasswordPage } from "@/app/pages/ForgotPasswordPage"
import { ResetPasswordPage } from "@/app/pages/ResetPasswordPage"
import { SelectRolePage } from "@/app/pages/SelectRolePage"
import { UnauthorizedPage } from "@/app/pages/UnauthorizedPage"
import { NotFoundPage } from "@/app/pages/NotFoundPage"
import { PlaceholderPage } from "@/app/pages/PlaceholderPage"
import { DashboardHomePage } from "@/app/pages/dashboard/DashboardHomePage"
import { SuperAdminDashboardPage } from "@/app/pages/dashboard/SuperAdminDashboardPage"
import { ClientDashboardPage } from "@/app/pages/dashboard/ClientDashboardPage"
import { RoleHomeRedirect } from "@/app/pages/RoleHomeRedirect"
import { ClientsListPage } from "@/app/pages/clients/ClientsListPage"
import { ClientCreatePage } from "@/app/pages/clients/ClientCreatePage"
import { ClientEditPage } from "@/app/pages/clients/ClientEditPage"
import { ClientDetailsPage } from "@/app/pages/clients/ClientDetailsPage"
import { ClientTrainersPage } from "@/app/pages/clients/ClientTrainersPage"
import { TrainersListPage } from "@/app/pages/trainers/TrainersListPage"
import { TrainerCreatePage } from "@/app/pages/trainers/TrainerCreatePage"
import { TrainerEditPage } from "@/app/pages/trainers/TrainerEditPage"
import { TrainerDetailsPage } from "@/app/pages/trainers/TrainerDetailsPage"
import { TrainerProfilePage } from "@/app/pages/trainer/TrainerProfilePage"
import { TrainerAvailabilityPage } from "@/app/pages/trainer/TrainerAvailabilityPage"
import { TrainerMeasurementsPage } from "@/app/pages/trainer/TrainerMeasurementsPage"
import { TrainerClientMeasurementsPage } from "@/app/pages/trainer/TrainerClientMeasurementsPage"
import { TrainerClientsPage } from "@/app/pages/trainer/TrainerClientsPage"
import { TrainerSessionNotesPage } from "@/app/pages/trainer/TrainerSessionNotesPage"
import { TrainerCheckInsPage } from "@/app/pages/trainer/TrainerCheckInsPage"
import { SubscriptionPlansListPage } from "@/app/pages/subscriptionPlans/SubscriptionPlansListPage"
import { SubscriptionPlanCreatePage } from "@/app/pages/subscriptionPlans/SubscriptionPlanCreatePage"
import { SubscriptionPlanEditPage } from "@/app/pages/subscriptionPlans/SubscriptionPlanEditPage"
import { SubscriptionsListPage } from "@/app/pages/subscriptions/SubscriptionsListPage"
import { SubscriptionCreatePage } from "@/app/pages/subscriptions/SubscriptionCreatePage"
import { SubscriptionDetailsPage } from "@/app/pages/subscriptions/SubscriptionDetailsPage"
import { ClientSubscriptionsPage } from "@/app/pages/client/ClientSubscriptionsPage"
import { ClientMeasurementsPage } from "@/app/pages/client/ClientMeasurementsPage"
import { SessionsListPage } from "@/app/pages/sessions/SessionsListPage"
import { SessionCreatePage } from "@/app/pages/sessions/SessionCreatePage"
import { SessionBulkCreatePage } from "@/app/pages/sessions/SessionBulkCreatePage"
import { SessionDetailsPage } from "@/app/pages/sessions/SessionDetailsPage"
import { SessionEditPage } from "@/app/pages/sessions/SessionEditPage"
import { TrainerSessionsListPage } from "@/app/pages/trainer/TrainerSessionsListPage"
import { TrainerSessionDetailsPage } from "@/app/pages/trainer/TrainerSessionDetailsPage"
import { ClientMySessionsListPage } from "@/app/pages/client/ClientMySessionsListPage"
import { ClientMySessionDetailsPage } from "@/app/pages/client/ClientMySessionDetailsPage"
import { ApplicationSettingsPage } from "@/app/pages/applicationSettings/ApplicationSettingsPage"
import { SuperAdminCheckInsPage } from "@/app/pages/checkIns/SuperAdminCheckInsPage"
import { SuperAdminMeasurementsPage } from "@/app/pages/measurements/SuperAdminMeasurementsPage"
import { Role, type RoleName } from "@/lib/constants"
import { NAV_ITEMS } from "@/lib/navigation"
import type { ReactNode } from "react"

const ROLE_SEGMENT: Record<RoleName, string> = {
  [Role.SUPER_ADMIN]: "super-admin",
  [Role.TRAINER]: "trainer",
  [Role.CLIENT]: "client",
}

/** Nested routes for a NAV_ITEMS entry that has grown beyond a single
 * placeholder screen, keyed by nav label. Task 22.3 implements the Clients
 * module and Task 22.4 the Trainers module (SUPER_ADMIN directory plus the
 * TRAINER self-profile and availability screens); other roles/sections stay
 * on PlaceholderPage. */
const SECTION_OVERRIDES: Partial<Record<RoleName, Record<string, Pick<RouteObject, "children">>>> = {
  [Role.SUPER_ADMIN]: {
    Clients: {
      children: [
        { index: true, element: <ClientsListPage /> },
        { path: "new", element: <ClientCreatePage /> },
        { path: ":id", element: <ClientDetailsPage /> },
        { path: ":id/edit", element: <ClientEditPage /> },
        { path: ":id/trainers", element: <ClientTrainersPage /> },
      ],
    },
    Trainers: {
      children: [
        { index: true, element: <TrainersListPage /> },
        { path: "new", element: <TrainerCreatePage /> },
        { path: ":id", element: <TrainerDetailsPage /> },
        { path: ":id/edit", element: <TrainerEditPage /> },
      ],
    },
    "Subscription Plans": {
      children: [
        { index: true, element: <SubscriptionPlansListPage /> },
        { path: "new", element: <SubscriptionPlanCreatePage /> },
        { path: ":id/edit", element: <SubscriptionPlanEditPage /> },
      ],
    },
    Subscriptions: {
      children: [
        { index: true, element: <SubscriptionsListPage /> },
        { path: "new", element: <SubscriptionCreatePage /> },
        { path: ":id", element: <SubscriptionDetailsPage /> },
      ],
    },
    Sessions: {
      children: [
        { index: true, element: <SessionsListPage /> },
        { path: "new", element: <SessionCreatePage /> },
        { path: "bulk", element: <SessionBulkCreatePage /> },
        { path: ":id", element: <SessionDetailsPage /> },
        { path: ":id/edit", element: <SessionEditPage /> },
      ],
    },
    "Check-ins": {
      children: [{ index: true, element: <SuperAdminCheckInsPage /> }],
    },
    Measurements: {
      children: [{ index: true, element: <SuperAdminMeasurementsPage /> }],
    },
    Settings: {
      children: [{ index: true, element: <ApplicationSettingsPage /> }],
    },
  },
  [Role.TRAINER]: {
    Sessions: {
      children: [
        { index: true, element: <TrainerSessionsListPage /> },
        { path: ":id", element: <TrainerSessionDetailsPage /> },
      ],
    },
    "Assigned Clients": {
      children: [{ index: true, element: <TrainerClientsPage /> }],
    },
    "Session Notes": {
      children: [{ index: true, element: <TrainerSessionNotesPage /> }],
    },
    "Check-ins": {
      children: [{ index: true, element: <TrainerCheckInsPage /> }],
    },
    Profile: {
      children: [{ index: true, element: <TrainerProfilePage /> }],
    },
    Measurements: {
      children: [{ index: true, element: <TrainerMeasurementsPage /> }],
    },
    Availability: {
      children: [{ index: true, element: <TrainerAvailabilityPage /> }],
    },
  },
  [Role.CLIENT]: {
    Subscriptions: {
      children: [{ index: true, element: <ClientSubscriptionsPage /> }],
    },
    "My Sessions": {
      children: [
        { index: true, element: <ClientMySessionsListPage /> },
        { path: ":id", element: <ClientMySessionDetailsPage /> },
      ],
    },
    Measurements: {
      children: [{ index: true, element: <ClientMeasurementsPage /> }],
    },
  },
}

/** Builds relative child routes for a role section from NAV_ITEMS, e.g.
 * "/super-admin/clients" -> relative path "clients" under the "super-admin" section.
 * "dashboard" is a real segment (matching ROLE_HOME_PATH), not an index route.
 * `dashboardElement` overrides the default placeholder-shell Dashboard page
 * for roles whose dashboard has been implemented (Task 22.2: Super Admin).
 * Nav items with a matching SECTION_OVERRIDES entry get real nested routes
 * instead of the placeholder-shell (Task 22.3: Clients). */
function roleSectionChildren(role: RoleName, dashboardElement: ReactNode = <DashboardHomePage />) {
  const prefix = `/${ROLE_SEGMENT[role]}/`

  return NAV_ITEMS[role].map((item) => {
    const relativePath = item.path.slice(prefix.length)
    const isDashboard = item.label === "Dashboard"
    const override = SECTION_OVERRIDES[role]?.[item.label]

    if (override) {
      return { path: relativePath, ...override }
    }

    return {
      path: relativePath,
      element: isDashboard ? dashboardElement : <PlaceholderPage title={item.label} />,
    }
  })
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/select-role", element: <SelectRolePage /> },
  { path: "/unauthorized", element: <UnauthorizedPage /> },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      { index: true, element: <RoleHomeRedirect /> },
      {
        path: ROLE_SEGMENT[Role.SUPER_ADMIN],
        element: <ProtectedRoute allowedRoles={[Role.SUPER_ADMIN]} />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { index: true, element: <Navigate to="dashboard" replace /> },
              ...roleSectionChildren(Role.SUPER_ADMIN, <SuperAdminDashboardPage />),
            ],
          },
        ],
      },
      {
        path: ROLE_SEGMENT[Role.TRAINER],
        element: <ProtectedRoute allowedRoles={[Role.TRAINER]} />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { index: true, element: <Navigate to="dashboard" replace /> },
              ...roleSectionChildren(Role.TRAINER),
              // Not a NAV_ITEMS entry (no sidebar link) - reached by clicking a
              // row on the Measurements page (Pending or All tab) or the
              // Assigned Clients list's "View Client" action. The bare
              // /trainer/clients index route above (SECTION_OVERRIDES
              // "Assigned Clients") is separate.
              { path: "clients/:id", element: <TrainerClientMeasurementsPage /> },
            ],
          },
        ],
      },
      {
        path: ROLE_SEGMENT[Role.CLIENT],
        element: <ProtectedRoute allowedRoles={[Role.CLIENT]} />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { index: true, element: <Navigate to="dashboard" replace /> },
              ...roleSectionChildren(Role.CLIENT, <ClientDashboardPage />),
            ],
          },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
])
