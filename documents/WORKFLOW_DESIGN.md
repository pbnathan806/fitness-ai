# WORKFLOW_DESIGN.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## User Authentication Workflow

1. Login.
2. Authenticate user.
3. Fetch assigned roles.
4. Display available dashboards.
5. Redirect to the selected dashboard.

### Business Rules

* Users may have multiple roles.
* Email shall be the username.
* Clients cannot self-register.
* Only Super Admins may assign roles.

---

## Role Switching Workflow

### Supported For

* Super Admin + Trainer

### Workflow

1. Login.
2. View assigned roles.
3. Select the required dashboard.
4. Continue operations.

### Business Rules

* Re-authentication is not required.
* Users may access only assigned roles.

---

## Client Onboarding Workflow

1. Super Admin creates the client.
2. Configure client's timezone.
3. Assign trainer.
4. Create subscription.
5. Configure weekly schedule.
6. Send account creation email.
7. Client account becomes active.

---

## Trainer Onboarding Workflow

1. Super Admin creates the trainer.
2. Configure trainer availability.
3. Assign trainer role.
4. Send account creation email.
5. Trainer account becomes active.

---

## Subscription Workflow

1. Create subscription.
2. Configure subscription start date.
3. Configure weekly schedule.
4. Assign trainer.
5. Activate subscription.

### Business Rules

* Subscriptions are for one month.
* Subscription may start on any date.
* Renewal is performed manually by Super Admins.
* Previous schedules shall be reused by default during renewal.
* Super Admins may modify schedules based on client requests.

---

## Session Workflow

1. Session is conducted.
2. Trainer records session notes.
3. Trainer submits trainer check-in.
4. Client progress information is updated.

---

## Session Reschedule Workflow

1. Client requests a one-time session change outside the application.
2. Super Admin validates trainer availability.
3. Session is rescheduled if possible.
4. Notifications are sent to affected users.

### Business Rules

* Session rescheduling is optional and subject to availability.
* Trainers may be reassigned if required.
* Super Admins exclusively manage reschedules.

---

## No Show Workflow

1. Client misses a session.
2. Super Admin marks the session as No Show.
3. Comments are recorded.
4. Notifications are sent if required.

---

## Subscription Renewal Workflow

1. Extend subscription by one month.
2. Reuse previous schedule by default.
3. Modify schedule if requested.
4. Activate renewed subscription.

---

## AI Workflow

1. Collect coaching information.
2. Queue AI processing asynchronously.
3. Generate coaching intelligence.
4. Human review is performed.
5. Reports are generated.
6. Notifications are sent.

### Business Rules

* AI shall never make operational decisions.
* Clients shall never directly access AI recommendations.
* Human review is mandatory before report sharing.

---

## Workflow Principles

1. Super Admin owns operational decisions.
2. Trainers own coaching decisions.
3. Clients own their progress tracking.
4. AI shall never block business workflows.
5. Historical records shall always be preserved.
6. Human decisions always take precedence over AI.
