# BACKEND_ARCHITECTURE.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Overview

The backend follows a modular monolithic architecture prioritizing simplicity, scalability and low operational cost.

---

## Technology Stack

| Component         | Technology     |
| ----------------- | -------------- |
| Backend           | FastAPI        |
| Database          | PostgreSQL     |
| ORM               | SQLAlchemy     |
| Authentication    | JWT            |
| Background Jobs   | Celery + Redis |
| AI Orchestration  | LangGraph      |
| LLM Framework     | LangChain      |
| Primary LLM       | Groq (Llama)   |
| API Documentation | OpenAPI        |
| Testing           | Pytest         |
| Containerization  | Docker         |

---

## Architecture

```text
                FastAPI
                    |
                API Layer
                    |
               Service Layer
                    |
            ------------------
            |                |
      Business Services    AI Services
            |                |
       PostgreSQL          Celery
                             |
                           Redis
                             |
                         Workers
                             |
                         LangGraph
                             |
                         LangChain
                             |
                           Groq
                             |
                           Llama
```

---

## Business Services

* Authentication Service
* Client Service
* Trainer Service
* Subscription Service
* Schedule Service
* Session Service
* Notification Service

---

## AI Services

* Report Service
* Coaching Intelligence Service
* Recommendation Service
* Trend Analysis Service

---

## Design Principles

1. AI shall never block business workflows.
2. AI shall always execute asynchronously.
3. Business services and AI services shall remain independent.
4. PostgreSQL shall remain the single source of truth.
5. Human review shall always take precedence over AI recommendations.

---

## Version-1 Constraints

Version-1 shall NOT support:

* Microservices.
* GraphQL.
* WebSockets.
* Kubernetes.
* Self-hosted LLMs.
* AI driven operational decisions.
