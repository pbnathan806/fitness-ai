# DATABASE_DESIGN.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## Overview

* PostgreSQL is the single source of truth.
* UUIDs shall be used for all primary keys.
* UTC shall be used for all timestamps.
* Historical records shall be preserved.

---

## Database Tables (19)

### Authentication

* users
* roles
* user_roles

### Client Management

* clients
* client_goals
* client_measurements
* client_check_ins

### Trainer Management

* trainers
* trainer_availability

### Subscription Management

* subscriptions

### Scheduling

* client_schedules
* sessions
* session_reschedules

### Coaching

* session_notes
* trainer_check_ins

### Reporting & AI

* reports
* ai_recommendations

### System

* notifications
* audit_logs

---

## Supported Roles

* Super Admin
* Trainer
* Client
* Super Admin + Trainer

### NOT Supported

* Client + Trainer
* Client + Super Admin
* Self-assigned roles

---

## User Role Relationships

* One User may have one or many roles.
* Role assignments are managed exclusively by Super Admins.

```text
roles
   |
user_roles
   |
 users
 /    \
/      \
clients trainers
```

---

## Audit Requirements

Applicable tables shall support:

* created_at
* updated_at
* created_by
* updated_by

---

## Common Status Values

Examples:

* ACTIVE
* EXPIRED
* CANCELLED
* COMPLETED
* RESCHEDULED
* GENERATED
* REVIEWED
* SENT
* FAILED

---

## Database Principles

1. Keep the database simple.
2. Preserve historical records.
3. PostgreSQL is the single source of truth.
4. AI exists only as an intelligence layer.
5. Human decisions always take precedence over automation.
6. Build only for approved Version-1 requirements.
