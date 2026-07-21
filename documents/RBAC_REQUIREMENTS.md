# RBAC_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Supported Roles

Version-1 supports the following roles:

* Super Admin
* Trainer
* Client

Version-1 shall NOT support:

* Custom roles.
* Delegated administration.
* Permission management by users.

---

# 2. Super Admin Responsibilities

Super Admins are responsible for:

* Client management.
* Trainer management.
* Subscription management.
* Schedule management.
* Trainer assignments.
* Session reschedules.
* Subscription renewals.
* Operational decisions.
* Report management.
* Managing operational exceptions.

---

# 3. Trainer Responsibilities

Trainers are responsible for:

* Conducting coaching sessions.
* Maintaining session notes.
* Recording client progress.
* Completing trainer check-ins.
* Reviewing coaching intelligence reports.
* Reviewing AI recommendations.
* Monitoring client adherence and progress.

Trainers shall have view-only access to:

* Client schedules.
* Subscription details.
* Trainer availability schedules.

Trainers shall NOT be able to:

* Manage subscriptions.
* Change client schedules.
* Assign trainers.
* Renew subscriptions.
* Make operational changes.

---

# 4. Client Responsibilities

Clients are responsible for:

* Maintaining their profile information.
* Completing client check-ins.
* Viewing their schedules.
* Tracking their progress.
* Viewing approved progress reports.
* Viewing subscription details.

Clients shall NOT be able to:

* Book sessions.
* Modify schedules through the application.
* Renew subscriptions.
* View AI recommendations.
* View coaching intelligence reports.
* Make operational changes.

---

# 5. Access Matrix

| Capability            | Client        | Trainer   | Super Admin |
| --------------------- | ------------- | --------- | ----------- |
| Manage Clients        | No            | No        | Yes         |
| Manage Trainers       | No            | No        | Yes         |
| Manage Subscriptions  | No            | No        | Yes         |
| Renew Subscriptions   | No            | No        | Yes         |
| Manage Schedules      | No            | View Only | Yes         |
| View Schedules        | Yes           | Yes       | Yes         |
| Client Check-ins      | Yes           | Yes       | Yes         |
| Trainer Check-ins     | No            | Yes       | Yes         |
| Session Notes         | View Own      | Yes       | Yes         |
| Progress Tracking     | Yes           | Yes       | Yes         |
| View Reports          | Yes (Limited) | Yes       | Yes         |
| AI Recommendations    | No            | Yes       | Yes         |
| Coaching Intelligence | No            | Yes       | Yes         |
| Password Management   | Yes           | Yes       | Yes         |
| Session Reschedules   | No            | No        | Yes         |
| Trainer Assignments   | No            | No        | Yes         |

---

# 6. AI Access Controls

| Capability            | Client | Trainer | Super Admin |
| --------------------- | ------ | ------- | ----------- |
| Progress Reports      | Yes    | Yes     | Yes         |
| AI Recommendations    | No     | Yes     | Yes         |
| Coaching Intelligence | No     | Yes     | Yes         |
| Risk Indicators       | No     | Yes     | Yes         |
| Trend Analysis        | No     | Yes     | Yes         |

Clients shall never have access to:

* Internal AI recommendations.
* Coaching intelligence reports.
* Risk indicators.
* Sensitive coaching observations.

---

# 7. Authentication Requirements

All roles shall support:

* Login.
* Logout.
* Password reset.
* Change password.
* Secure session management.

Version-1 shall NOT support:

* Social login.
* Multi-factor authentication.
* Single Sign-On (SSO).

---

# 8. Version-1 Constraints

Version-1 shall NOT support:

* Additional roles.
* Custom permissions.
* Role hierarchies.
* Delegated administration.
* Client managed schedules.
* Trainer managed subscriptions.
* AI driven permissions.

---

# 9. Version-1 Principles

1. Super Admins own all operational decisions.
2. Trainers own coaching responsibilities.
3. Clients own their coaching journey.
4. Human decisions shall always take precedence over automation.
5. Access shall be granted on a least privilege basis.
6. AI recommendations shall remain restricted to Trainers and Super Admins.
