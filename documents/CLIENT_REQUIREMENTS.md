# CLIENT_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Overview

Clients are at the center of the coaching experience. The application provides premium human-led coaching, progress tracking and coaching intelligence through trainer-approved reports. Clients do not perform operational activities through the application.

---

# 2. Client Responsibilities

Clients are responsible for:

* Maintaining their profile information.
* Completing client check-ins.
* Tracking their progress.
* Attending scheduled coaching sessions.
* Reviewing their progress reports.
* Communicating schedule change requests to Super Admins outside the application.

---

# 3. Client Profile Management

Clients shall be able to:

* View their profile information.
* Update permitted profile information.
* Change their password.
* View their assigned trainer information.
* View their configured timezone information.
* View their subscription details.

Version-1 shall NOT support:

* Client self-registration.

---

# 4. Subscription Management

Clients shall be able to:

* View their subscription details.
* View subscription start and end dates.
* View subscription renewal information.

Clients shall NOT be able to:

* Create subscriptions.
* Renew subscriptions.
* Modify subscriptions.
* Cancel subscriptions through the application.

> Subscription management shall be performed exclusively by Super Admins.

---

# 5. Schedule Management

Clients shall be able to:

* View their coaching schedules.
* View session details.
* View session reschedule information.
* View trainer change information.

Clients shall NOT be able to:

* Book coaching sessions.
* Modify schedules through the application.
* Perform session reschedules.
* Assign or change trainers.

> Clients may manually request permanent schedule changes or one-time session reschedules by contacting Super Admins outside the application.

---

# 6. Coaching Journey

Clients shall be able to:

* Complete client check-ins.
* Track their progress.
* View historical progress information.
* View completed sessions.
* View upcoming sessions.
* View milestone achievements.

Progress information may include:

* Weight changes.
* Body measurements.
* Goal progress.
* Session completion statistics.
* Workout consistency.
* Milestone achievements.

---

# 7. Reports

Clients shall have access to:

* Weekly progress reports.
* Monthly progress reports.
* Progress tracking reports.
* Trainer approved coaching summaries.
* Historical progress reports.

Clients shall NOT have access to:

* AI recommendations.
* Coaching intelligence reports.
* Risk indicators.
* Sensitive coaching observations.
* Business reports.

---

# 8. Notifications

Clients shall receive email notifications for:

* Account creation.
* Subscription creation.
* Subscription renewals.
* Upcoming session reminders.
* Session reschedules.
* Session cancellations.
* Trainer changes.
* Subscription expiry reminders.
* Weekly and monthly progress reports.
* Password reset requests.

---

# 9. Timezone Requirements

1. Clients may belong to any valid global IANA timezone.
2. Clients shall always view schedules and reports in their configured timezone.
3. The application shall automatically handle all timezone conversions and Daylight Saving Time (DST) changes.
4. Clients shall never be required to perform manual timezone calculations.

---

# 10. Access Restrictions

Clients shall NOT be able to:

* Book sessions.
* Manage subscriptions.
* Manage schedules.
* Assign or change trainers.
* View internal AI recommendations.
* View coaching intelligence reports.
* Perform operational approvals.
* Modify historical records.

---

# 11. Version-1 Constraints

Version-1 shall NOT support:

* Client self-registration.
* Client managed schedules.
* Client managed subscriptions.
* Multiple subscription plans.
* Direct interactions with AI.
* Operational decision making by clients.
* Mobile applications.

---

# 12. Client Principles

1. Clients own their coaching journey and progress updates.
2. Super Admins own all operational decisions.
3. Trainers own coaching responsibilities.
4. Human-centered premium coaching is the foundation of the product.
5. Technology shall quietly enable exceptional coaching experiences.
6. Coaching intelligence shall assist trainers and Super Admins in delivering better client outcomes.
