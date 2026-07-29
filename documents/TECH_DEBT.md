# Technical Debt

Tracked shortcuts and known gaps, recorded with the context needed to fix
them later. Add new items to the top.

---

## Enhance CheckInResponse with submitted_by_role and submitted_by_name

**Recorded:** 2026-07-30 (Check-ins V2, Module 7 - Super Admin frontend integration)

**What:** `CheckInResponse` exposes `submitted_by` as a bare user id. The
frontend (SUPER_ADMIN's Session Details "Submitted By" field) can only
positively identify a **CLIENT** submitter, because `ClientRepository`
exposes the client's `user_id` but `TrainerResponse`/`TrainerRepository`
never expose a trainer's underlying `user_id` (only their trainer profile
id). A submission by the assigned TRAINER and one by a SUPER_ADMIN are
therefore indistinguishable client-side today; both render as the fallback
label "Trainer or Super Admin".

**Why deferred:** Fixing this requires a backend change (either expose
`user_id` on the trainer API, or - cleaner - add `submitted_by_role` and
`submitted_by_name` directly to `CheckInResponse`, resolved server-side
where the full identity graph is already available). That was explicitly
out of scope for Module 7 (frontend-only integration) per user instruction
("Do not make any backend changes").

**Fix:**
- Add `submitted_by_role: RoleName` and `submitted_by_name: str` to
  `backend/schemas/check_in.py::CheckInResponse`, resolved in
  `CheckInService` (or the router's `_to_response`) by cross-referencing
  `submitted_by` against the session's client/trainer/assignment records
  already loaded, falling back to SUPER_ADMIN only when neither matches.
- Update `frontend/src/types/checkIn.ts` and
  `frontend/src/app/pages/sessions/components/SessionCheckInCard.tsx` to
  use the new fields directly instead of the `resolveSubmittedBy` client-side
  guess (`frontend/src/app/pages/sessions/SessionDetailsPage.tsx` currently
  supplies that resolver - it can be deleted once the backend fields land).
- Update the corresponding backend/frontend tests.

**Current behavior (accepted for MVP):** display only two buckets -
"{client name} (Client)" or "Trainer or Super Admin".
