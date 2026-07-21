# SUPER_ADMIN_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Overview

Super Admins own all operational responsibilities within the application. They are responsible for managing clients, trainers, subscriptions, schedules and operational exceptions while ensuring exceptional coaching experiences.

---

# 2. Super Admin Responsibilities

Super Admins are responsible for:

* Client management.
* Trainer management.
* Subscription management.
* Schedule management.
* Trainer assignments.
* Subscription renewals.
* Session reschedules.
* Managing operational exceptions.
* Reviewing coaching intelligence reports.
* Managing business reports.

---

# 3. Client Management

Super Admins shall be able to:

* Create client accounts.
* Update client information.
* View client profiles.
* Assign and reassign trainers.
* Manage client subscriptions.
* View historical client records.
* Configure client timezones.

---

# 4. Subscription Management

Super Admins shall be able to:

* Create subscriptions.
* Renew subscriptions.
* Extend subscriptions.
* Modify future subscription schedules.
* View historical subscription records.

Subscription requirements:

* Version-1 supports monthly subscriptions only.
* Subscriptions may begin on any day of the month.
* Previous schedules shall be selected by default during subscription renewals.
* Super Admins may modify schedules during renewals based on client preferences.

---

# 5. Schedule Management

Super Admins shall be able to:

* Create recurring client schedules.
* Modify future schedules.
* Perform one-time session reschedules.
* Assign replacement trainers when required.
* Mark sessions as client no-shows with comments.
* View historical schedule information.

Clients may request:

* Permanent schedule changes.
* One-time session reschedules.

> All schedule related changes are subject to trainer availability.

---

# 6. Trainer Management

Super Admins shall be able to:

* Create trainer accounts.
* Update trainer information.
* Manage trainer availability.
* Assign and reassign trainers.
* View trainer schedules.
* View trainer utilization reports.
* View historical trainer information.

---

# 7. Session Management

Super Admins shall be able to:

* View all sessions.
* Perform session reschedules.
* Assign replacement trainers.
* Mark client no-shows.
* View session histories.
* Manage session related operational exceptions.

Super Admins shall NOT perform coaching activities unless operationally required.

---

# 8. Coaching Intelligence

Super Admins shall be able to:

* View coaching intelligence reports.
* View AI recommendations.
* Review high-risk client indicators.
* Review adherence trends.
* Review projected progress trends.
* Monitor coaching outcomes across clients.

> Human review shall always take precedence over AI recommendations.

---

# 9. Reports

Super Admins shall have access to:

* Weekly business reports.
* Subscription reports.
* Trainer utilization reports.
* Client retention reports.
* Session statistics.
* Coaching intelligence reports.
* Subscription expiry reports.
* Historical business reports.

---

# 10. Notifications

Super Admins shall receive email notifications for:

* Account creation.
* Subscription creation.
* Subscription renewals.
* Subscription expiry alerts.
* Trainer assignments and changes.
* Session reschedules.
* Weekly business reports.
* Password reset requests.

---

# 11. Timezone Requirements

1. Super Admins shall operate exclusively in the Asia/Kolkata timezone.
2. The application shall automatically perform all timezone conversions.
3. Client schedules shall be configured using the client's configured timezone.
4. Super Admins shall never be required to perform manual timezone calculations.

---

# 12. Access Restrictions

Super Admins shall NOT:

* Delegate operational ownership to AI.
* Permit AI driven operational decisions.
* Modify historical records unless explicitly authorized through application workflows.

---

# 13. Version-1 Constraints

Version-1 shall NOT support:

* Multiple subscription plans.
* Client managed schedules.
* Trainer managed subscriptions.
* AI driven operational decisions.
* Delegated administration.
* Custom roles and permissions.

---

# 14. Super Admin Principles

1. Super Admins own all operational decisions.
2. Human decisions shall always take precedence over automation.
3. Operational simplicity shall be prioritized at all times.
4. Historical records shall be preserved.
5. Exceptional coaching experiences remain the primary objective of the platform.
6. Coaching intelligence exists to assist operational and coaching decisions and not replace them.
