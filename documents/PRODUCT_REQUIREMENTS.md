# PRODUCT_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Product Overview

The platform is a human-centered premium online coaching platform that combines operational simplicity, exceptional coaching experiences and AI-assisted coaching intelligence.

The platform enables:

* Monthly coaching subscriptions.
* Fixed recurring coaching schedules.
* Premium human-led coaching.
* AI-assisted coaching intelligence.
* Beautiful and actionable progress reports.
* Operational simplicity through Super Admin managed workflows.

---

# 2. Version-1 Scope

Version-1 includes:

* Monthly subscriptions.
* Fixed recurring schedules.
* Client management.
* Trainer management.
* Session management.
* Subscription renewals.
* Session reschedules.
* Progress tracking.
* Client and Trainer check-ins.
* Coaching intelligence.
* AI-assisted reports.
* Email notifications.
* Timezone-aware scheduling.
* Role based access control.
* Historical record preservation.

---

# 3. Supported Roles

Version-1 supports:

* Super Admin
* Trainer
* Client

---

# 4. Subscription Model

1. Version-1 supports monthly subscriptions only.
2. Subscriptions may begin on any day of the month.
3. Subscription renewals are performed by Super Admins.
4. Previous schedules shall be selected by default during renewals.
5. Super Admins may modify schedules during renewals based on client preferences.
6. Clients shall manually communicate renewal requests outside the application.

---

# 5. Scheduling Model

1. Clients are assigned fixed recurring schedules.
2. Clients do not book sessions through the application.
3. Super Admins manage all schedules.
4. Clients may request permanent schedule changes outside the application.
5. Clients may request one-time session reschedules outside the application.
6. Session reschedules are subject to trainer availability.
7. Super Admins shall manage all schedule changes and operational exceptions.

---

# 6. Coaching Model

1. Coaching sessions are human-led.
2. Trainers are responsible for coaching activities.
3. Clients and Trainers shall both complete check-ins.
4. Trainers shall maintain session notes and progress updates.
5. Human decisions shall always take precedence over automation.

---

# 7. Timezone Management

1. Clients may belong to any valid global IANA timezone.
2. Trainers and Super Admins shall operate exclusively in Asia/Kolkata.
3. The client's timezone is the source of truth for coaching schedules.
4. All timestamps shall be stored internally in UTC.
5. The application shall automatically handle timezone conversions and DST changes.

---

# 8. AI Capabilities

Version-1 AI capabilities include:

* Progress analysis.
* Trend analysis.
* Coaching intelligence.
* Recommendation generation.
* Session note summarization.
* Weekly and monthly report generation.
* Pattern detection.

AI shall NOT support:

* Operational decisions.
* Session scheduling.
* Subscription management.
* Trainer assignments.
* Autonomous workflows.

---

# 9. Reporting

Version-1 supports:

* Weekly progress reports.
* Monthly progress reports.
* Coaching intelligence reports.
* Progress tracking reports.
* Trainer reports.
* Super Admin business reports.

Reports shall prioritize:

* Coaching outcomes.
* Client delight.
* Actionable insights.

---

# 10. Notifications

Version-1 supports:

* Email notifications only.

Notifications include:

* Account creation.
* Subscription updates.
* Session updates.
* Subscription expiry reminders.
* Progress reports.
* Password reset requests.

Notifications shall never affect business operations.

---

# 11. Historical Records

1. Historical records shall be preserved.
2. Future schedule changes shall not modify historical records.
3. Historical reports shall remain immutable.
4. Historical subscriptions and session records shall never be automatically modified.

---

# 12. Version-1 Constraints

Version-1 shall NOT support:

* Multiple subscription plans.
* Client session bookings.
* Client managed schedules.
* Mobile applications.
* SMS notifications.
* WhatsApp notifications.
* AI driven operational decisions.
* Custom roles and permissions.
* Marketplace capabilities.
* Corporate plans.
* Social login and Single Sign-On (SSO).

---

# 13. Product Principles

1. Build the Minimum Exceptional Product (MEP).
2. Prioritize exceptional coaching experiences over feature richness.
3. Prioritize operational simplicity.
4. Human beings own coaching and operational decisions.
5. AI exists to assist humans and not replace them.
6. Technology shall quietly enable exceptional coaching experiences.
7. Version-1 succeeds when clients experience exceptional coaching rather than technological sophistication.

---

# 14. Project Motto

> "We are building the Minimum Exceptional Product—a human-centered premium coaching intelligence platform that quietly enables exceptional coaching experiences through operational simplicity and AI-assisted intelligence."
