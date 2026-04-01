# Student Dashboard V2 - Step 3A API Mapping and Migration Decision

## Objective
- Map each Student Dashboard V2 section to current backend endpoints.
- Identify endpoint gaps before integration.
- Define which student dashboard to keep and when to remove the legacy version.

## Current Dual-Dashboard State
- Production route: `/student` -> `StudentDashboardV2.vue`.
- Compatibility route: `/student-v2` -> `StudentDashboardV2.vue`.
- Legacy fallback route: `/student-legacy` -> `StudentDashboard.vue`.

Decision:
- Cutover is complete: V2 is now the default student dashboard.
- Keep `StudentDashboard.vue` only as a rollback-safe fallback during stabilization.
- Remove legacy route and view only after stabilization checks pass.

## Keep/Remove Plan
1. Current state after cutover:
- `StudentDashboardV2.vue` is default on `/student`.
- `StudentDashboard.vue` is available only on `/student-legacy`.

2. Stabilization window:
- Keep the legacy fallback route for one release cycle.
- Track any production issues against V2 and validate regression gates.

3. Remove point:
- If no issues after stabilization, remove `/student-legacy` and delete legacy view usage.

## V2 Section -> API Contract Map

### Dashboard Home
UI blocks:
- Summary cards
- Recent applications
- Unread notifications badge

Use now:
- `GET /student/dashboard`

Response fields used:
- `data.summary`
- `data.recent_applications`
- `data.unread_notifications`

Status:
- Available

### My Applications
UI blocks:
- Table, status filter, search filter, pagination, timeline, offer actions

Use now:
- `GET /student/applications?status=&q=&page=&limit=`
- `PUT /student/offers/{offer_id}/respond` (accept/reject)

Response fields used:
- `data.items`
- `data.total`
- `data.page`
- `data.pages`
- `data.limit`
- Item fields include drive/company/interview/offer/timeline payload

Status:
- Available

### Notifications
UI blocks:
- List, unread count, mark one read, mark all read, optional filter

Use now:
- `GET /student/notifications?is_read=&page=&limit=`
- `PUT /student/notifications/{notification_id}/read`
- `PUT /student/notifications/read-all`

Response fields used:
- `data.items`
- `data.unread_count`

Status:
- Available

### Profile
UI blocks:
- Profile form save

Use now:
- `GET /student/profile`
- `PUT /student/profile`

Payload now:
- `college_name`
- `branch`
- `year`
- `cgpa`
- `roll_number`
- `phone`
- `resume_url`
- `skills`
- `experience_summary`

Status:
- Available

### Drives
UI blocks:
- Drive browsing, search/filter, apply action

Use now:
- `GET /student/drives`
- `POST /student/drives/{drive_id}/apply`

Status:
- Available

### History and Documents
UI blocks:
- Placement history timeline/cards
- Offer letter or placement confirmation download

Use now:
- `GET /student/history`
- `GET /student/offers/{offer_id}/document`
- `GET /student/placements/{placement_id}/document`

Status:
- Available

## Integration Order (Step 3B onward)
1. Stabilize V2 as default:
- Keep `/student` mapped to V2 and monitor post-cutover behavior.

2. Keep rollback path during observation:
- Keep `/student-legacy` for one release cycle.

3. Remove legacy after observation:
- Remove fallback route and legacy dashboard once stable.

## Test and Review Gates
Per slice:
- Backend: run student and related pytest modules.
- Frontend: run vitest suite.
- Manual responsive check at desktop/tablet/mobile widths.

Before cutover:
- Full backend suite pass
- Full frontend suite pass
- Route-level smoke check for `/student` and `/student-v2`

## Git Checkpoint Pattern
- Commit after each stable slice.
- Push after each stable slice.

Suggested commit sequence:
1. `feat(student-v2): wire dashboard summary recent applications notifications`
2. `feat(student-v2): wire applications timeline and offer response`
3. `feat(student-v2): wire student profile save with current schema`
4. `feat(student-api): add drives listing and apply endpoints`
5. `feat(student-api): add history and document download endpoints`
6. `chore(student-v2): cutover /student route to v2 and retain legacy backup`
7. `chore(student-v2): remove legacy dashboard after stabilization`
