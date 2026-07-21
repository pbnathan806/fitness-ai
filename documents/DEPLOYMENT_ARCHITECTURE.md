# DEPLOYMENT_ARCHITECTURE.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## Technology Stack

| Component        | Technology                |
| ---------------- | ------------------------- |
| Frontend         | React + TypeScript + Vite |
| Backend          | FastAPI                   |
| Database         | PostgreSQL                |
| Background Jobs  | Celery + Redis            |
| AI Orchestration | LangGraph                 |
| LLM Framework    | LangChain                 |
| Primary LLM      | Groq (Llama)              |
| Deployment       | Render                    |
| Emails           | Resend                    |
| CI/CD            | GitHub Actions            |
| Containerization | Docker                    |

---

## Deployment Architecture

```text
                        USERS
                          |
                       Internet
                          |
                       Frontend
                        Render
                          |
                        FastAPI
                        Render
                          |
                     PostgreSQL
                        Render
                          |
                         Redis
                        Render
                          |
                     Celery Workers
                        Render
                          |
                 -------------------------
                 |                       |
            Notifications             AI Services
                 |                       |
               Resend                LangGraph
                                         |
                                     LangChain
                                         |
                                    Model Router
                                         |
                                        Groq
                                         |
                                       Llama
                                         |
                               Coaching Intelligence
                                         |
                           --------------------------------
                           |                              |
                        Reports                    Recommendations
                           |                              |
                            --------------------------------
                                         |
                                    Human Review
                                         |
                                Final Reports Generated
```

---

## Production Components

The following components shall be deployed for Version-1:

* Frontend Service
* Backend Service
* PostgreSQL Database
* Redis Instance
* Celery Workers
* AI Services
* Notification Services
* Email Services
* Groq Integration

---

## Supported Environments

Version-1 shall support:

* Development
* Production

---

## Deployment Principles

1. Render shall be the primary hosting platform.
2. PostgreSQL shall remain the single source of truth.
3. AI services shall always execute asynchronously.
4. AI failures shall never affect business operations.
5. Production deployments shall be automated using GitHub Actions.
6. Human review shall always take precedence over AI recommendations.
7. Operational simplicity shall always be preferred over architectural complexity.

---

## Render Services

The following services shall be maintained in Version-1:

* Frontend Service
* Backend Service
* PostgreSQL Database
* Redis Instance
* Celery Worker Service

> Version-1 intentionally limits the number of deployed services to maintain operational simplicity and reduce infrastructure costs.

---

## Version-1 Constraints

Version-1 shall NOT support:

* Kubernetes.
* Microservices.
* AWS.
* Azure.
* GCP.
* Self-hosted LLMs.
* GPU Servers.
* Multiple deployment environments beyond Development and Production.

---

## Infrastructure Principles

1. If Render can support a requirement, no additional infrastructure shall be introduced.
2. AI exists solely as an asynchronous Coaching Intelligence layer.
3. Business services shall remain independent of AI services.
4. Build only approved Version-1 requirements.
5. Keep infrastructure simple, maintainable and cost-effective.
