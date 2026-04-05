# Recruitify

Recruitify is a full-stack placement portal built with Flask, Vue.js, SQLite, Redis, and Celery.
It supports role-based workflows for students, companies, and admins across drives,
applications, interviews, offers, and background job automation.

## Background Jobs Environment (Simple Defaults)

Set these in your environment when running job features.

| Variable | Default | Purpose |
| --- | --- | --- |
| CELERY_BROKER_URL | redis://127.0.0.1:6379/0 | Redis broker for Celery queue |
| CELERY_RESULT_BACKEND | redis://127.0.0.1:6379/1 | Redis result backend |
| JOBS_EAGER_EXECUTION | false | true runs jobs inline, false uses queue |
| JOBS_DAILY_REMINDER_CRON | 0 9 * * * | Daily deadline reminder schedule |
| JOBS_INTERVIEW_REMINDER_ENABLED | false | Enable interview reminder job |
| JOBS_INTERVIEW_REMINDER_CRON | 30 9 * * * | Interview reminder schedule |
| JOBS_INTERVIEW_REMINDER_WINDOW_HOURS | 24 | Look-ahead window for interviews |
| JOBS_REMINDER_CHANNELS | email | Default reminder channels |
| JOBS_INTERVIEW_REMINDER_CHANNELS | falls back to JOBS_REMINDER_CHANNELS | Interview reminder channels |
| JOBS_WEBHOOK_URL | empty | Optional webhook target URL |
| JOBS_MONTHLY_REPORT_CRON | 0 9 1 * * | Monthly report schedule |
| JOBS_MONTHLY_REPORT_AUDIENCE | admin | admin, company, or both |
| JOBS_MONTHLY_REPORT_FORMAT | html | html or pdf |
| JOBS_COMPANY_EXPORT_ENABLED | false | Enable company export endpoints |
| JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY | false | Enable company placement export |
| JOBS_EXPORT_ARTIFACT_TTL_HOURS | 24 | Export download expiry |

Note: sms and webhook are optional. Core project submission flow works with email only.

## Production-Like Runbook (Non-Eager)

1. Start Redis:
	- docker run -d --name recruitify-redis -p 6379:6379 redis:7-alpine
2. Start backend API from backend folder:
	- d:/ASHISH/PROJECT/recruitify_23F3000163/.venv/Scripts/python.exe run.py
3. Start Celery worker from backend folder:
	- d:/ASHISH/PROJECT/recruitify_23F3000163/.venv/Scripts/python.exe -m celery -A celery_worker.celery worker --loglevel=info --pool=solo
4. Start Celery beat from backend folder:
	- d:/ASHISH/PROJECT/recruitify_23F3000163/.venv/Scripts/python.exe -m celery -A celery_beat.celery beat --loglevel=info
5. Check queue health:
	- GET /jobs/health
6. Trigger and verify jobs:
	- Interview reminders
	- Monthly reports (admin/company)
	- Student and company exports

## Rollback Point

Safe rollback tag for this release line:

- rollback-2026-04-06-safe

Recommended rollback workflow:

1. git fetch --tags
2. git switch -c rollback-2026-04-06 rollback-2026-04-06-safe
3. Deploy from this rollback branch/reference.

## Safe Checkpoint History

Recent safe checkpoints on main:

- 1f89945 chore: add feature flags for remaining jobs scope
- aed84ad feat: add scheduled interview reminders with safe retries
- 2bc0b96 feat: support company and pdf monthly reports
- 013b301 feat: add company and placement async export jobs
- 65ae8a1 chore: simplify reminder channels
- 514a7b1 test: add jobs hardening checks
