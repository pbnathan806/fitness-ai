# REPORT_REQUIREMENTS.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Overview

Reports are a core differentiator of the product. They shall provide meaningful, actionable and easy-to-understand coaching insights while prioritizing client delight and coaching outcomes.

---

# 2. Report Principles

1. Reports shall prioritize coaching outcomes and client delight.
2. Reports shall be simple, actionable and easy to understand.
3. Historical reports shall remain immutable.
4. Reports shall be generated asynchronously using background jobs.
5. Human review shall always take precedence over AI recommendations.
6. Reports shall never affect business operations.

---

# 3. Client Reports

Clients shall have access to:

* Weekly progress reports.
* Monthly progress reports.
* Goal tracking summaries.
* Progress trends.
* Session statistics.
* Subscription details.
* Trainer approved coaching summaries.
* Historical progress reports.

Client reports may include:

* Weight changes.
* Body measurement changes.
* Goal achievement summaries.
* Workout consistency.
* Session completion statistics.
* Milestone achievements.
* Progress trends.

Clients shall NOT have access to:

* AI recommendations.
* Coaching intelligence reports.
* Risk indicators.
* Sensitive coaching observations.
* Business reports.

---

# 4. Trainer Reports

Trainers shall have access to:

* Client progress reports.
* Weekly coaching reports.
* Monthly coaching reports.
* Session summaries.
* Client adherence reports.
* Progress trend analysis.
* Coaching intelligence reports.
* AI recommendations.
* High-risk client indicators.
* Historical coaching reports.

---

# 5. Super Admin Reports

Super Admins shall have access to:

* Weekly business reports.
* Subscription reports.
* Trainer utilization reports.
* Client retention reports.
* Session statistics.
* Coaching intelligence summaries.
* AI recommendations.
* Subscription expiry reports.
* Trainer assignment summaries.
* Historical business reports.

---

# 6. Coaching Intelligence Reports

AI generated coaching intelligence reports may include:

* Progress trends.
* Goal achievement trends.
* Plateau detection.
* Session adherence analysis.
* Missed session trends.
* Client engagement insights.
* Coaching recommendations.
* Projected progress trends.
* Risk indicators.

> All coaching recommendations are subject to human review.

---

# 7. Session Reports

Session reports may include:

* Session completion status.
* Session notes.
* Client check-in summaries.
* Trainer check-in summaries.
* Historical session information.
* Coaching observations.

---

# 8. Report Visibility

| Report Type                 | Client        | Trainer | Super Admin |
| --------------------------- | ------------- | ------- | ----------- |
| Weekly Reports              | Yes           | Yes     | Yes         |
| Monthly Reports             | Yes           | Yes     | Yes         |
| Progress Reports            | Yes           | Yes     | Yes         |
| Session Reports             | Yes (Limited) | Yes     | Yes         |
| AI Recommendations          | No            | Yes     | Yes         |
| Coaching Intelligence       | No            | Yes     | Yes         |
| Risk Indicators             | No            | Yes     | Yes         |
| Business Reports            | No            | No      | Yes         |
| Trainer Utilization Reports | No            | No      | Yes         |

---

# 9. Technical Requirements

1. Reports shall be generated asynchronously using background jobs.
2. Report generation failures shall never affect business operations.
3. Historical reports shall never be automatically modified.
4. Report timestamps shall be stored internally in UTC.
5. Reports shall support timezone aware displays.
6. AI generated insights shall not modify business data.

---

# 10. Historical Records

1. Historical reports shall remain immutable.
2. Future schedule changes shall not modify historical reports.
3. Subscription renewals shall preserve historical report data.
4. Historical coaching intelligence reports shall be preserved for audit purposes.

---

# 11. Version-1 Constraints

Version-1 shall NOT support:

* Custom report builders.
* Advanced BI dashboards.
* Report exports.
* Client access to internal AI recommendations.
* Client access to sensitive coaching intelligence.
* AI driven coaching decisions.

---

# 12. Reporting Principles

1. Reports exist to improve coaching outcomes and client delight.
2. Reports shall prioritize clarity over complexity.
3. Human review shall always take precedence over AI generated recommendations.
4. Coaching intelligence exists to assist Trainers and Super Admins.
5. Reports shall remain independent of business operations.
