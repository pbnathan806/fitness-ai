# FOLDER_STRUCTURE.md

## Status

* FROZEN (Version-1)

## Version

* 1.1

---

## Project Structure

```text
fitness-ai/

│
├── backend/
│
│   ├── app/
│   │
│   ├── api/
│   │
│   ├── core/
│   │      ├── config.py
│   │      ├── security.py
│   │      └── constants.py
│   │
│   ├── database/
│   │      ├── session.py
│   │      └── base.py
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── repositories/
│   │
│   ├── services/
│   │
│   ├── ai/
│   │      ├── graphs/
│   │      ├── prompts/
│   │      ├── models/
│   │      ├── router/
│   │      ├── reports/
│   │      └── recommendations/
│   │
│   ├── workers/
│   │
│   ├── notifications/
│   │
│   ├── utils/
│   │
│   └── main.py
│
│
│   ├── tests/
│   │
│   ├── alembic/
│   │
│   ├── requirements/
│   │
│   └── Dockerfile
│
│
├── frontend/
│
│   ├── src/
│   │
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── contexts/
│   ├── hooks/
│   ├── routes/
│   ├── utils/
│   └── assets/
│
│
├── docs/
│
├── scripts/
│
├── .github/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore

```

---

## Backend Modules

* Authentication
* Clients
* Trainers
* Subscriptions
* Scheduling
* Coaching
* Notifications
* Reports
* AI Services

---

## AI Modules

* LangGraph Graphs
* LangChain Integrations
* Model Router
* Prompt Templates
* Report Generation
* Coaching Intelligence
* Recommendations

---

## Frontend Modules

* Authentication
* Super Admin Dashboard
* Trainer Dashboard
* Client Dashboard
* Reports
* Notifications
* Progress Tracking

---

## Folder Structure Principles

1. Keep business services separate from AI services.
2. Keep all AI-related code inside the `ai` module.
3. Maintain clear separation between API, Service, Repository and Database layers.
4. Keep Version-1 implementation simple and modular.
5. Follow a modular monolithic architecture.
