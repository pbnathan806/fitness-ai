# SECURITY_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## Overview

Version-1 security requirements are designed to provide secure access control while maintaining operational simplicity.

---

## Authentication

* JWT based authentication.
* Secure password hashing.
* Time-limited password reset links.
* Email shall be the username.
* Multiple roles per user are supported.

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

> Role assignments are managed exclusively by Super Admins.

---

## Authorization

* Role-based access control (RBAC) is mandatory.
* APIs shall validate assigned roles before processing requests.
* Users shall access only authorized dashboards and APIs.
* Unauthorized access attempts shall be denied and logged.

---

## Session Security

* JWT tokens shall be required for authenticated APIs.
* Users may switch between assigned roles without re-authentication.
* Logout shall invalidate active sessions.
* Password reset links shall have an expiry time.

---

## Data Security

* HTTPS shall be mandatory.
* UTC shall be used for all timestamps.
* Sensitive information shall never be logged.
* API requests shall be validated before processing.
* Input sanitization shall be enforced where applicable.

---

## Audit Requirements

The following activities shall be audited:

* Login activities.
* Role assignments.
* Client updates.
* Trainer updates.
* Subscription changes.
* Schedule changes.
* Session reschedules.
* No Show updates.
* Report generation status changes.
* Password reset requests.

---

## AI Security

* AI shall have read-only access to business data.
* AI recommendations shall always require human review.
* Clients shall never have access to internal AI recommendations.
* AI shall never make operational decisions.

---

## Notification Security

* Notifications shall be sent only to authorized users.
* Password reset emails shall use secure, time-limited links.
* Report notifications shall not expose sensitive information.

---

## Version-1 Constraints

Version-1 shall NOT support:

* Multi-factor authentication (MFA).
* Single Sign-On (SSO).
* Social logins.
* Public APIs.
* Third-party authentication providers.
* AI driven operational decisions.

---

## Security Principles

1. Human decisions always take precedence over AI.
2. Least privilege access shall be enforced.
3. Historical records shall always be preserved.
4. Security shall remain operationally simple.
5. AI shall exist only as a Coaching Intelligence layer.
6. Operational failures shall never compromise business data.
