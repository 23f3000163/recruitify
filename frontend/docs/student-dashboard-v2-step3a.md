# Student Dashboard V2 - Step 3A API Mapping and Migration Decision

## Objective
- Map each Student Dashboard V2 section to current backend endpoints.
- Identify endpoint gaps before integration.
- Define which student dashboard to keep and when to remove the legacy version.

## Current Dual-Dashboard State
- Legacy production route: `/student` -> `StudentDashboard.vue`.
- V2 preview route: `/student-v2` -> `StudentDashboardV2.vue`.

Decision:
- Keep BOTH dashboards temporarily during migration.
- Keep `StudentDashboard.vue` as the production-safe fallback until V2 reaches feature parity.
- Keep `StudentDashboardV2.vue` as the active implementation target.
- Remove legacy only after parity checks, regression tests, and route cutover are complete.

## Keep/Remove Plan
1. Keep now:
- Keep `StudentDashboard.vue` untouched for rollback safety.
- Continue integrating data into `StudentDashboardV2.vue`.

2. Cutover point:
- After V2 parity + tests pass, route `/student` to `StudentDashboardV2.vue`.
- Move legacy to `StudentDashboardLegacy.vue` for one release cycle.

3. Remove point:
- If no issues after the release cycle, remove legacy view and cleanup related dead code.

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
- `PUT /student/profile`

Payload today:
- `college_name`
- `branch`
- `year`
- `cgpa`
- `roll_number`

Status:
- Available but limited to academic profile fields
Gap:
- V2 visual profile includes extra fields (phone, linkedin, github, skill tags, resume metadata) that are not yet persisted by current endpoint schema.

### Drives
UI blocks:
- Drive browsing, search/filter, apply action

Use now:
- No student drives listing/apply endpoints found in current student blueprint.

Status:
- Missing
Needed endpoints:
- `GET /student/drives` with query/filter/pagination
- `POST /student/drives/{drive_id}/apply` with duplicate apply protection

### History and Documents
UI blocks:
- Placement history timeline/cards
- Offer letter or placement confirmation download

Use now:
- No dedicated student history/download endpoints found in current student blueprint.

Status:
- Missing
Needed endpoints:
- `GET /student/history`
- `GET /student/offers/{offer_id}/document` OR `GET /student/placements/{placement_id}/document`

## Integration Order (Step 3B onward)
1. Wire available APIs first:
- Dashboard home
- Applications
- Notifications
- Offer response
- Profile save (current schema)

2. Add missing backend endpoints next:
- Drives list/apply
- History and document download

3. Route cutover:
- Switch `/student` to V2 after full parity + test pass

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
