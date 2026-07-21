# AI_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. AI Principles

1. AI is an intelligence layer only.
2. AI shall never make operational decisions.
3. AI failures shall never affect business operations.
4. Human approval shall always take precedence over AI recommendations.
5. AI shall have read-only access to application data through application services.
6. Clients shall not directly interact with AI in Version-1.

---

# 2. AI Responsibilities

AI shall support:

* Progress analysis.
* Historical trend analysis.
* Weekly report generation.
* Monthly report generation.
* Coaching intelligence.
* Recommendation generation.
* Session note summarization.
* Pattern detection.
* Adherence analysis.
* Goal progress analysis.
* Plateau detection.
* Missed session trend analysis.

---

# 3. AI Restrictions

AI shall NOT support:

* Subscription management.
* Session scheduling.
* Trainer assignments.
* Session cancellations.
* Operational approvals.
* Database modifications.
* Autonomous decision making.
* Direct client interactions.

---

# 4. AI Visibility

| Capability            | Client | Trainer | Super Admin |
| --------------------- | ------ | ------- | ----------- |
| Progress Reports      | Yes    | Yes     | Yes         |
| Weekly Reports        | Yes    | Yes     | Yes         |
| Monthly Reports       | Yes    | Yes     | Yes         |
| AI Recommendations    | No     | Yes     | Yes         |
| Coaching Intelligence | No     | Yes     | Yes         |
| Risk Indicators       | No     | Yes     | Yes         |
| Trend Analysis        | No     | Yes     | Yes         |

---

# 5. Coaching Intelligence

AI may provide insights such as:

* Progress trends.
* Goal achievement trends.
* Workout consistency analysis.
* Session adherence analysis.
* Plateau detection.
* Missed session patterns.
* Coaching recommendations.
* Projected progress trends.
* Client engagement insights.

> All coaching recommendations are subject to human review.

---

# 6. Report Generation

AI shall support:

* Weekly progress reports.
* Monthly progress reports.
* Coaching intelligence reports.
* Session note summaries.
* Historical progress summaries.

Reports shall be generated asynchronously using background jobs.

---

# 7. Human Review Requirements

The following shall require human review before being shared with clients:

* Coaching recommendations.
* Risk indicators.
* Intervention recommendations.
* Goal modification recommendations.
* Sensitive coaching observations.

Version-1 shall not expose internal AI reasoning to clients.

---

# 8. Technical Requirements

Version-1 shall use:

* LangGraph for AI orchestration.
* FastAPI for AI services.
* PostgreSQL as the source of truth.
* Background jobs for report generation.
* Application services for data access.

AI services shall remain loosely coupled with business services.

---

# 9. Version-1 Constraints

Version-1 shall NOT support:

* AI chatbots.
* AI based operational decisions.
* Autonomous AI workflows.
* Voice interactions.
* AI based trainer assignments.
* AI based scheduling.
* Client interactions with AI.

---

# 10. Version-1 Scope

Version-1 AI capabilities are limited to:

* Coaching intelligence.
* Progress analysis.
* Trend analysis.
* Report generation.
* Recommendation generation.
* Pattern detection.
* Session note summarization.

> AI exists to assist coaches and Super Admins in delivering exceptional coaching experiences. Human beings remain responsible for all coaching and operational decisions.
