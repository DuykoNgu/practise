# Plan — M1 Access

- **Goal:** every role can log in and out, sees only permitted navigation, and maintains their own profile.
- **Depends on:** M0
- **Docs:** [03-use-cases.md](../../docs/03-use-cases.md), [04-information-architecture.md](../../docs/04-information-architecture.md), [business-rules.md](../../docs/requirements/business-rules.md), [class diagrams §1](../../docs/architecture/uml/01-class-diagrams.md), [sequence §1](../../docs/architecture/uml/02-sequence-diagrams.md#1-login--post-apiv1authlogin)

## M1-1 SCR-01 Login and logout

| Field | Value |
|---|---|
| Stories / AC | US01, US02 · AC-UC01, AC-UC02 |
| Rules / NFR | BR-001, BR-021 · NFR-SEC-001, NFR-SEC-002, NFR-SEC-003, NFR-SEC-005 |
| API | `POST /auth/login`, `POST /auth/logout` |
| Tables | `app_users`, `audit_logs` |
| Design | Sequence §1; class diagrams §1 Authentication |
| Backend modules | `auth`, `users` (repository read), `audit` (`AuditService.record` only) |
| Frontend | `app/(public)/login`, `features/auth`, logout action in the shell topbar |

**Backend**
- [ ] `auth` router, service, schemas per openapi.yaml
- [ ] Disabled users cannot log in; generic error message for wrong email or password
- [ ] 5 failed attempts per account per 15 minutes → `429` (see Open)
- [ ] Audit events `LOGIN`, `LOGOUT`
- [ ] `audit` module: `AuditService.record` and repository (screen comes in M6-1)

**Frontend**
- [ ] Login form (react-hook-form + zod), visible labels, error focus
- [ ] Token storage and session state; redirect to dashboard after login
- [ ] Logout in topbar returns to login

**Tests**
- [ ] Success, wrong password, disabled user, rate limit `429`, token expiry, audit written
- [ ] Form validation and error states

**Done when:** AC-UC01 and AC-UC02 pass for all four roles.

**Open:** Q-15 (where the failed-login counter is stored).

## M1-2 SCR-90 Forbidden

| Field | Value |
|---|---|
| Stories / AC | Cross-cutting authorization · UI/UX state contract "Forbidden" |
| Rules / NFR | BR-001, NFR-SEC-004 |
| API | — |
| Frontend | Forbidden page with a safe route back; `proxy.ts` role guard |

**Frontend**
- [ ] Forbidden page keeps authentication and offers a link to the dashboard
- [ ] Role guard sends unauthorized routes to the forbidden page

**Tests**
- [ ] Each role hitting a forbidden route lands on the forbidden page

**Done when:** every route in the IA page-permission table is enforced in the UI.

**Open:** I-04 (route `/403` in IA vs folder `forbidden/`).

## M1-3 SCR-80 Profile

| Field | Value |
|---|---|
| Stories / AC | US18 · AC-UC19 |
| Rules / NFR | BR-001, BR-021 · NFR-SEC-002 |
| API | `GET /profile`, `PUT /profile`, `POST /profile/password` |
| Tables | `app_users`, `audit_logs` |
| Backend modules | `users` |
| Frontend | `(workspace)/profile`, `features/profile`; tabs Account, Security, Roles and permissions |

**Backend**
- [ ] Profile read and update; role is never changed through the profile
- [ ] Password change requires the current password; minimum 8 characters
- [ ] Audit events for profile update and password change

**Frontend**
- [ ] Three tabs; read-only role and permissions tab
- [ ] Validation errors keep input and focus the first invalid field

**Tests**
- [ ] Role cannot be changed; wrong current password; short password; audit written

**Done when:** AC-UC19 passes.
