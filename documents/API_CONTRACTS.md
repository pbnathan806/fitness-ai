# API_CONTRACTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## Overview

* REST APIs only.
* JWT based authentication.
* Role based authorization.
* APIs shall remain stateless.
* AI operations shall execute asynchronously.

---

## Authentication APIs

| Method | Endpoint                     |
| ------ | ---------------------------- |
| POST   | /api/v1/auth/login           |
| POST   | /api/v1/auth/logout          |
| POST   | /api/v1/auth/forgot-password |
| POST   | /api/v1/auth/reset-password  |
| GET    | /api/v1/auth/me              |
| GET    | /api/v1/auth/roles           |
| POST   | /api/v1/auth/switch-role     |

---

## Client APIs

| Method | Endpoint                          |
| ------ | --------------------------------- |
| GET    | /api/v1/clients                   |
| GET    | /api/v1/clients/{id}              |
| POST   | /api/v1/clients                   |
| PUT    | /api/v1/clients/{id}              |
| GET    | /api/v1/clients/{id}/goals        |
| POST   | /api/v1/clients/{id}/goals        |
| GET    | /api/v1/clients/{id}/measurements |
| POST   | /api/v1/clients/{id}/measurements |
| GET    | /api/v1/clients/{id}/check-ins    |
| POST   | /api/v1/clients/{id}/check-ins    |

---

## Trainer APIs

| Method | Endpoint                           |
| ------ | ---------------------------------- |
| GET    | /api/v1/trainers                   |
| GET    | /api/v1/trainers/{id}              |
| POST   | /api/v1/trainers                   |
| PUT    | /api/v1/trainers/{id}              |
| GET    | /api/v1/trainers/{id}/availability |
| PUT    | /api/v1/trainers/{id}/availability |

> Trainer availability shall be managed by Super Admins in Version-1.

---

## Subscription APIs

| Method | Endpoint                          |
| ------ | --------------------------------- |
| POST   | /api/v1/subscriptions             |
| GET    | /api/v1/subscriptions/{id}        |
| PUT    | /api/v1/subscriptions/{id}/renew  |
| PUT    | /api/v1/subscriptions/{id}/extend |

---

## Schedule APIs

| Method | Endpoint                           |
| ------ | ---------------------------------- |
| POST   | /api/v1/schedules                  |
| GET    | /api/v1/schedules/{id}             |
| PUT    | /api/v1/schedules/{id}             |
| GET    | /api/v1/sessions                   |
| GET    | /api/v1/sessions/{id}              |
| POST   | /api/v1/sessions/{id}/reschedule   |
| POST   | /api/v1/sessions/{id}/mark-no-show |

> Session reschedules and No Show updates are managed exclusively by Super Admins.

---

## Coaching APIs

| Method | Endpoint                       |
| ------ | ------------------------------ |
| POST   | /api/v1/session-notes          |
| GET    | /api/v1/session-notes/{id}     |
| POST   | /api/v1/trainer-check-ins      |
| GET    | /api/v1/trainer-check-ins/{id} |

---

## Reporting APIs

| Method | Endpoint             |
| ------ | -------------------- |
| GET    | /api/v1/reports      |
| GET    | /api/v1/reports/{id} |

> Report generation shall execute asynchronously.

---

## AI APIs

| Method | Endpoint                      |
| ------ | ----------------------------- |
| GET    | /api/v1/ai-recommendations    |
| GET    | /api/v1/coaching-intelligence |

> Clients shall never have direct access to AI recommendation APIs.

---

## Notification APIs

| Method | Endpoint              |
| ------ | --------------------- |
| GET    | /api/v1/notifications |

---

## Authorization Principles

* Multiple roles per user are supported.
* Users may access only assigned roles.
* Role assignments are managed exclusively by Super Admins.
* APIs shall enforce role based authorization.

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

## Asynchronous Operations

The following operations shall execute asynchronously:

* AI analysis.
* Report generation.
* Notification delivery.
* Coaching intelligence generation.
* Weekly report generation.
* Monthly report generation.

---

## Version-1 Constraints

Version-1 shall NOT support:

* GraphQL.
* WebSockets.
* Public APIs.
* Third-party integrations.
* AI driven operational APIs.
* AI driven scheduling.
* AI driven subscription management.

---

## API Principles

1. APIs shall remain thin.
2. Business logic shall reside in service layers.
3. AI shall never block business workflows.
4. Human decisions shall always take precedence over AI recommendations.
5. Operational simplicity shall always be preferred over architectural complexity.
