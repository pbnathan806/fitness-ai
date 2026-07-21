# NOTIFICATION_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Overview

Notifications are intended to keep users informed about important coaching and operational events. Notifications are informational only and shall never affect business operations.

---

# 2. Supported Notification Channels

Version-1 supports:

* Email Notifications

Version-1 shall NOT support:

* SMS Notifications.
* WhatsApp Notifications.
* Push Notifications.
* In-App Notifications.
* Marketing Notifications.

---

# 3. Notification Principles

1. Notifications are informational only.
2. Failed notifications shall never block business operations.
3. Notifications shall be sent asynchronously using background jobs.
4. Notification preferences are not configurable in Version-1.
5. All notifications shall display timestamps in the recipient's timezone.
6. Business workflows shall not depend on successful notification delivery.

---

# 4. Client Notifications

Clients shall receive notifications for:

* Account creation.
* Subscription creation.
* Subscription renewals.
* Upcoming session reminders.
* Session reschedules.
* Session cancellations.
* Trainer changes.
* Subscription expiry reminders.
* Weekly progress reports.
* Monthly progress reports.
* Password reset requests.

---

# 5. Trainer Notifications

Trainers shall receive notifications for:

* Account creation.
* Trainer assignments.
* Upcoming session reminders.
* Session reschedules.
* Session cancellations.
* Client schedule changes.
* Weekly coaching reports.
* Password reset requests.

---

# 6. Super Admin Notifications

Super Admins shall receive notifications for:

* Account creation.
* Subscription creation.
* Subscription renewals.
* Subscription expiry alerts.
* Trainer assignments and changes.
* Session reschedules.
* Weekly business reports.
* Password reset requests.

---

# 7. Session Notifications

Notifications shall be sent for:

* Upcoming sessions.
* Session reschedules.
* Session cancellations.
* Trainer changes.
* Client no-show updates (Trainer and Super Admin only).

---

# 8. Subscription Notifications

Notifications shall be sent for:

* New subscriptions.
* Subscription renewals.
* Subscription expiry reminders.
* Successful subscription extensions.

---

# 9. Report Notifications

Notifications shall be sent for:

* Weekly progress reports.
* Monthly progress reports.
* Coaching report availability.
* Weekly business report availability.

> Clients shall never receive notifications containing internal AI recommendations or sensitive coaching intelligence.

---

# 10. Timezone Requirements

1. Clients shall receive notifications in their configured timezone.
2. Trainers shall receive notifications in Asia/Kolkata.
3. Super Admins shall receive notifications in Asia/Kolkata.
4. The application shall automatically handle timezone conversions and Daylight Saving Time (DST) changes.

---

# 11. Technical Requirements

1. Notifications shall be delivered asynchronously using background jobs.
2. Notification failures shall be logged for operational visibility.
3. Notification delivery failures shall not affect application workflows.
4. Notification timestamps shall be stored internally in UTC.

---

# 12. Version-1 Constraints

Version-1 shall NOT support:

* Notification preference management.
* Custom notification templates.
* SMS notifications.
* WhatsApp notifications.
* Push notifications.
* Marketing campaigns.
* Promotional emails.

---

# 13. Notification Principles

1. Notifications exist to improve the coaching experience.
2. Notifications shall remain simple and actionable.
3. Business operations shall continue regardless of notification delivery status.
4. Users shall never be required to perform any business operation through notifications.
