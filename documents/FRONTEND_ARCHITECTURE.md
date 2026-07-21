# FRONTEND_ARCHITECTURE.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Overview

The frontend follows a role-based architecture prioritizing simplicity, responsiveness and ease of maintenance.

---

## Technology Stack

| Component        | Technology                |
| ---------------- | ------------------------- |
| Frontend         | React                     |
| Language         | TypeScript                |
| Build Tool       | Vite                      |
| State Management | Context API + React Query |
| UI Framework     | Tailwind CSS              |
| Routing          | React Router              |
| API Integration  | Axios                     |

---

## Roles

* Super Admin
* Trainer
* Client

---

## Modules

### Super Admin

* Dashboard
* Client Management
* Trainer Management
* Subscription Management
* Schedule Management
* Session Management
* Reports
* Notifications

### Trainer

* Dashboard
* Assigned Clients
* Sessions
* Session Notes
* Trainer Check-ins
* Reports

### Client

* Dashboard
* Profile
* Progress Tracking
* Client Check-ins
* Reports
* Notifications

---

## Design Principles

1. Responsive design for desktop and mobile browsers.
2. Role-based dashboards.
3. JWT based authentication.
4. Role-based route protection.
5. Timezone aware displays.
6. Minimal and intuitive user experience.

---

## Version-1 Constraints

Version-1 shall NOT support:

* Mobile applications.
* Offline support.
* Dark mode.
* Multi-language support.
* Real-time notifications.
* Client self-registration.
