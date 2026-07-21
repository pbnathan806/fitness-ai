# TIMEZONE_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Overview

The application shall provide automatic timezone management for all coaching activities. Clients shall always view schedules and reports in their configured timezone, while Trainers and Super Admins shall operate exclusively in the Asia/Kolkata timezone.

---

# 2. Timezone Principles

1. The client's timezone is the source of truth for all coaching schedules.
2. The application owns all timezone conversions and complexity.
3. Users shall never be required to perform manual timezone calculations.
4. All timestamps shall be stored internally in UTC.
5. The application shall automatically handle Daylight Saving Time (DST) changes.

---

# 3. Supported Timezones

1. Clients may belong to any valid global IANA timezone.
2. Trainers shall operate exclusively in Asia/Kolkata.
3. Super Admins shall operate exclusively in Asia/Kolkata.
4. Version-1 shall support all valid IANA timezone identifiers.

Examples include:

* America/New_York
* America/Chicago
* America/Denver
* America/Los_Angeles
* America/Phoenix
* America/Anchorage
* Pacific/Honolulu
* Europe/London
* Asia/Dubai
* Asia/Singapore
* Asia/Kolkata

> The application is not limited to the above examples.

---

# 4. Client Requirements

Clients shall:

* View schedules in their configured timezone.
* View reports in their configured timezone.
* Receive notifications in their configured timezone.

Clients shall NOT:

* Perform manual timezone conversions.
* Modify session timings directly through the application.

---

# 5. Trainer Requirements

Trainers shall:

* View schedules in Asia/Kolkata.
* Receive notifications in Asia/Kolkata.
* View client schedules automatically converted to Asia/Kolkata.

Trainers shall NOT:

* Perform manual timezone conversions.
* Modify timezone configurations.

---

# 6. Super Admin Requirements

Super Admins shall:

* Configure client schedules using the client's timezone.
* View schedules in Asia/Kolkata.
* Manage timezone related operational activities.

Super Admins shall NOT:

* Perform manual timezone conversions.

---

# 7. Scheduling Requirements

1. Client schedules shall be created using the client's timezone.
2. Session timings shall automatically be converted for Trainers and Super Admins.
3. Daylight Saving Time (DST) changes shall be automatically handled by the application.
4. Future schedule changes shall not modify historical session records.
5. Session reminders shall use the recipient's timezone.

---

# 8. Technical Requirements

1. All timestamps shall be stored internally in UTC.
2. The client's configured timezone shall be stored as an IANA timezone identifier.
3. Timezone conversions shall be performed by the application layer.
4. Historical records shall preserve their original UTC timestamps.
5. Timezone conversions shall never modify business data.

---

# 9. Historical Records

1. Historical schedules shall remain immutable.
2. Historical reports shall preserve their original timestamps.
3. Future timezone or schedule changes shall not modify historical records.
4. Subscription renewals shall preserve historical subscription information.

---

# 10. Version-1 Constraints

Version-1 shall NOT support:

* User configurable timezone preferences.
* Manual timezone conversions.
* Multiple timezone configurations for a single user.
* Trainer specific timezone management.
* Super Admin timezone customization.

---

# 11. Timezone Principles

1. The client's timezone is the source of truth.
2. UTC is the application's internal source of truth.
3. The application shall hide all timezone complexity from users.
4. Users shall always see date and time information relevant to their role and timezone.
5. Timezone management shall never affect business operations.
