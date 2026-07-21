# USER_STORIES.md

## Status

* FROZEN (Version-1)

## Version

* 1.0

## Last Updated

* 20-Jul-2026

---

# 1. Super Admin User Stories

### Client Management

* As a Super Admin, I should be able to create client accounts.
* As a Super Admin, I should be able to update client profiles.
* As a Super Admin, I should be able to assign trainers to clients.
* As a Super Admin, I should be able to manage client subscriptions.
* As a Super Admin, I should be able to renew subscriptions.
* As a Super Admin, I should be able to view historical subscription records.

### Schedule Management

* As a Super Admin, I should be able to create recurring client schedules.
* As a Super Admin, I should be able to modify future schedules based on client requests.
* As a Super Admin, I should be able to perform one-time session reschedules based on trainer availability.
* As a Super Admin, I should be able to mark sessions as client no-shows with comments.
* As a Super Admin, I should be able to assign replacement trainers when required.
* As a Super Admin, I should be able to preserve historical schedule records.

### Trainer Management

* As a Super Admin, I should be able to create trainer accounts.
* As a Super Admin, I should be able to manage trainer availability.
* As a Super Admin, I should be able to assign and reassign trainers.
* As a Super Admin, I should be able to view trainer utilization reports.

### Reporting

* As a Super Admin, I should be able to view business reports.
* As a Super Admin, I should be able to review coaching intelligence reports.
* As a Super Admin, I should be able to review AI recommendations before coaching interventions.
* As a Super Admin, I should be able to view historical reports.

---

# 2. Trainer User Stories

### Coaching

* As a Trainer, I should be able to view my assigned clients.
* As a Trainer, I should be able to view my upcoming sessions.
* As a Trainer, I should be able to conduct coaching sessions.
* As a Trainer, I should be able to record session notes.
* As a Trainer, I should be able to update client progress information.
* As a Trainer, I should be able to complete trainer check-ins.

### Schedule Management

* As a Trainer, I should be able to view my schedule.
* As a Trainer, I should be able to view trainer availability information.
* As a Trainer, I should not be able to modify schedules or trainer availability.

### Coaching Intelligence

* As a Trainer, I should be able to view coaching intelligence reports.
* As a Trainer, I should be able to review AI recommendations.
* As a Trainer, I should be able to monitor client adherence trends.
* As a Trainer, I should be able to identify clients requiring coaching interventions.

---

# 3. Client User Stories

### Profile Management

* As a Client, I should be able to view and update my profile information.
* As a Client, I should be able to view my subscription details.
* As a Client, I should be able to view my assigned trainer information.

### Coaching Journey

* As a Client, I should be able to view my coaching schedule.
* As a Client, I should be able to complete client check-ins.
* As a Client, I should be able to track my progress.
* As a Client, I should be able to view weekly and monthly progress reports.
* As a Client, I should be able to view historical progress reports.

### Scheduling

* As a Client, I should not be able to book coaching sessions.
* As a Client, I should not be able to modify schedules through the application.
* As a Client, I should be able to manually request permanent schedule changes outside the application.
* As a Client, I should be able to manually request one-time session reschedules outside the application.

---

# 4. AI User Stories

* As a Trainer, I should receive AI-assisted coaching insights for my clients.
* As a Super Admin, I should receive AI-assisted coaching recommendations.
* As a Trainer, I should receive adherence and progress trend analyses.
* As a Super Admin, I should receive coaching intelligence summaries.
* As a Client, I should receive trainer-approved progress reports.

> Clients shall never have direct access to AI recommendations or sensitive coaching intelligence.

---

# 5. Notification User Stories

* As a Client, I should receive email notifications related to my subscription, schedules and reports.
* As a Trainer, I should receive email notifications related to my coaching responsibilities.
* As a Super Admin, I should receive email notifications related to operational activities.

---

# 6. Timezone User Stories

* As a Client, I should always view schedules and reports in my configured timezone.
* As a Trainer, I should always view schedules in Asia/Kolkata.
* As a Super Admin, I should always view schedules in Asia/Kolkata.
* As a User, I should never be required to manually perform timezone conversions.

---

# 7. Version-1 Constraints

* Clients cannot book sessions.
* Trainers cannot modify schedules.
* Trainers cannot manage subscriptions.
* Clients cannot view internal AI recommendations.
* AI cannot perform operational decisions.
* Business operations shall continue even when AI services are unavailable.
* Historical records shall never be automatically modified.
