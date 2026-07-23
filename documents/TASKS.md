# TASKS.md

## Status

* ACTIVE

## Last Updated

* 23-Jul-2026

---

## Task-20 — Application Settings Module

### Status

* COMPLETE (approved and implemented 23-Jul-2026)

### Summary

Introduce a configurable, DB-backed Application Settings module so operational
thresholds (currently hardcoded elsewhere) are stored in `application_settings`
and read through a settings service. This lands as a standalone, fully usable
module. Dashboard integration was originally scoped into this task, but on
investigation no Dashboard module exists yet in the codebase — building it
from scratch is a second module in its own right, so it has been split out
into [[Task-21]] to respect Rule 1 (never implement multiple modules).

### Scope

**New module**

* `models/application_setting.py`
* `repositories/application_setting_repository.py`
* `services/application_setting_service.py`
* `schemas/application_setting.py`
* `routers/application_settings.py` (registered in `main.py`)

(Paths adapted to this repo's actual layout — `backend/<layer>/`, not
`app/<layer>/`.)

**Database**

* New table `application_settings` (`id`, `key` UNIQUE NOT NULL, `value` NOT NULL,
  `description` nullable, `created_at`, `updated_at`) via Alembic migration.
* Seed data: `measurement_overdue_days = 14`, `subscription_expired_days = 30`.

**Settings service API**

* `get_int(key) -> int`
* `get_string(key) -> str`
* `get_bool(key) -> bool`

**API endpoints (SUPER_ADMIN only)**

* `GET /api/v1/application-settings`
* `GET /api/v1/application-settings/{key}`
* `PATCH /api/v1/application-settings/{key}`

**Business rules formalized (for consumption by Task-21, not implemented here)**

* ACTIVE: `today <= end_date`
* EXPIRED: `end_date < today` and `(today - end_date) <= subscription_expired_days`
* INACTIVE: `(today - end_date) > subscription_expired_days`

### Out of scope (moved to Task-21)

* Trainer / Super Admin / Client dashboard endpoints and calculations.
* ACTIVE/EXPIRED/INACTIVE computation wired into any consuming service.

### Tests required

1. Application settings CRUD (service layer)
2. `get_int` / `get_string` / `get_bool` typed accessors, including invalid-value errors
3. SUPER_ADMIN-only access enforcement on all three endpoints
4. Regression — existing functionality unaffected

### Acceptance Criteria

1. All tests pass.
2. SUPER_ADMIN can create-time-seed and modify settings via PATCH; other roles are forbidden.
3. No hardcoded operational values are introduced by this module.
4. Existing functionality remains unaffected (backward compatible).

### Deliverables (on completion)

1. Modified/created files
2. Alembic migration filename
3. Seed data inserted
4. Commands executed
5. Test results
6. Query optimization notes

---

## Task-21 — Dashboard Module (Trainer / Super Admin / Client)

### Status

* COMPLETE (implemented 23-Jul-2026)

### Summary

Built the Dashboard module from scratch: three role-scoped read-only
endpoints under `/api/v1/dashboard/{trainer,super-admin,client}`, wired to
[[Task-20]]'s Application Settings (`measurement_overdue_days`,
`subscription_expired_days`) instead of hardcoded values.

### Blockers resolved before implementation (user decisions, 23-Jul-2026)

1. **`target_check_ins` source**: added `SubscriptionPlan.sessions_per_week`
   (nullable Integer) and snapshotted it onto `Subscription.plan_sessions_per_week`
   at purchase time, mirroring the existing plan-snapshot pattern
   (`plan_name`, `plan_price`, etc.). Additive migration
   `dd617a9bfa18_add_sessions_per_week_to_subscription_.py`. Wired through
   `subscription_plan`/`subscription` schemas, services, and routers.
2. **ACTIVE/EXPIRED/INACTIVE source**: computed independently from
   `end_date` + `subscription_expired_days` (per Task-20's formulas),
   ignoring the existing stored `Subscription.status` enum
   (ACTIVE/EXPIRED/PAUSED/CANCELLED) entirely for dashboard purposes. A
   PAUSED or CANCELLED subscription with a future `end_date` will read as
   ACTIVE in dashboard counts — a known tradeoff of computing purely from
   dates, accepted explicitly by the user.

### Judgment calls made during implementation (not asked, documented here for review)

1. **`pending_check_ins` vs `clients_missing_check_ins_today`**: the original
   spec defined both under the "Super Admin Dashboard" heading, but only
   `pending_check_ins` appears in the SUPER ADMIN RESPONSE example (actually
   inside the TRAINER RESPONSE example) — `clients_missing_check_ins_today`
   never appears in either example JSON. Treated these as the same
   computation at different scope: `pending_check_ins` = trainer's assigned
   clients only (Trainer dashboard), `clients_missing_check_ins_today` =
   all clients (Super Admin dashboard, added beyond the literal example).
2. **Day/week/month framing**: Trainer and Super Admin dashboards are framed
   in Asia/Kolkata per TIMEZONE_REQUIREMENTS.md (today/this-week/this-month
   = IST calendar boundaries, including for "has this client checked in
   today" within `pending_check_ins`). The Client dashboard's
   `check_ins_this_week` (Monday-Sunday) and 90-day adherence window are
   framed in that client's own timezone.
3. **`sessions_today` / `upcoming_sessions_next_7_days`** exclude CANCELLED
   sessions (counting a cancelled session as "today's session" would
   mislead the viewer). "Next 7 days" is a 7-day window starting today
   (IST), so it overlaps with `sessions_today` by design.
4. Clients with zero subscriptions are excluded from the
   active/expired/inactive buckets entirely (not forced into one), so
   `active + expired + inactive` may be less than `total_clients`.
5. `check_in_adherence_percentage` is `0` (not null/error) when a client has
   zero expected sessions in the trailing 90 days.

### Modified/created files

* `models/subscription_plan.py`, `models/subscription.py` (additive columns)
* `schemas/subscription_plan.py`, `schemas/subscription.py`,
  `services/subscription_plan_service.py`, `services/subscription_service.py`,
  `routers/subscription_plans.py`, `routers/subscriptions.py` (sessions_per_week wiring)
* `utils/dashboard.py` (new — date-range helpers, ACTIVE/EXPIRED/INACTIVE and
  measurement-overdue classifiers)
* `repositories/client_repository.py`, `repositories/session_repository.py`,
  `repositories/check_in_repository.py`, `repositories/measurement_repository.py`,
  `repositories/subscription_repository.py` (additive aggregate methods)
* `repositories/dashboard_repository.py` (new)
* `services/dashboard_service.py` (new)
* `schemas/dashboard.py`, `routers/dashboard.py` (new), `main.py` (router registered)
* Tests: `tests/utils/test_dashboard.py`, `tests/services/test_dashboard_service.py`,
  `tests/routers/test_dashboard.py` (39 new tests), plus new abstract methods
  backfilled into existing Fake repositories in
  `tests/services/test_client_service.py`, `test_session_service.py`,
  `test_check_in_service.py`, `test_measurement_service.py`,
  `test_subscription_service.py` so those ABCs stay instantiable.

### Alembic migrations

* `dd617a9bfa18_add_sessions_per_week_to_subscription_.py` (revises `13dee62a63b4`)

### Commands executed

* `alembic revision --autogenerate -m "add sessions_per_week to subscription plans and subscriptions"`
  (hand-trimmed the same unrelated `password_reset_tokens` drift artifact as Task-20)
* `alembic upgrade head`
* Direct-query smoke test against real Postgres for the window-function and
  `NOT EXISTS` queries (`get_latest_end_dates_for_clients`,
  `get_latest_recorded_at_for_clients`, `count_pending_check_ins`,
  `count_total_trainers`, `count_all`) — confirmed they execute without
  syntax errors against the actual DB, not just fakes.
* `pytest -q` (full suite)

### Test results

516/517 passed. The one failure (`test_measurements.py::test_health_endpoint_unaffected`)
is the same pre-existing, unrelated full-suite-ordering flake noted in Task-20
(passes in isolation; reproduces with dashboard files excluded too).

### Query optimization notes

* `get_latest_end_dates_for_clients` / `get_latest_recorded_at_for_clients`
  use a single `ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY ...)`
  query each instead of one query per client (avoids N+1 across all clients
  or a trainer's whole roster).
* `count_pending_check_ins` is one query with a correlated `NOT EXISTS`
  subquery joining `sessions` and `check_ins`, instead of fetching sessions
  and check-ins separately and joining in Python.
* All dashboard counts use `SELECT COUNT(*)` server-side rather than
  fetching rows into the app.
* `subscription_plans.sessions_per_week` and `subscriptions.plan_sessions_per_week`
  are plain nullable columns (no new index) since they're only read per-row,
  never filtered/sorted on.
* No new index was added for the dashboard queries beyond what already
  exists (`subscriptions.client_id`, `sessions.client_id`/`trainer_id`,
  `check_ins.client_id` are all FK-indexed already); revisit if
  `total_clients`/`total_trainers` scale far beyond Version-1 expectations.

### Example dashboard responses

Trainer (`GET /api/v1/dashboard/trainer`):
```json
{
  "assigned_clients": 18,
  "active_clients": 17,
  "sessions_today": 5,
  "upcoming_sessions_next_7_days": 20,
  "pending_check_ins": 2,
  "pending_measurements": 3
}
```

Super Admin (`GET /api/v1/dashboard/super-admin`):
```json
{
  "total_clients": 150,
  "active_clients": 120,
  "expired_clients": 15,
  "inactive_clients": 15,
  "total_trainers": 10,
  "sessions_today": 25,
  "upcoming_sessions_next_7_days": 80,
  "measurements_recorded_this_month": 200,
  "check_ins_submitted_today": 95,
  "clients_missing_check_ins_today": 4
}
```

Client (`GET /api/v1/dashboard/client`):
```json
{
  "check_ins_this_week": 2,
  "target_check_ins": 3,
  "check_in_adherence_percentage": 87
}
```
