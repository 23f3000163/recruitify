# Recruitify

Recruitify is a full-stack placement portal built with Flask, Vue.js, SQLite, Redis, and Celery.
It supports role-based workflows for students, companies, and admins across drives,
applications, interviews, offers, and background job automation.





## Production-Like Runbook 

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

## Switching between DAILY and DEMO mode

1. Open `backend/app/jobs/celery_app.py`.
2. In `beat_schedule`, comment the `daily-reminder-placeholder` block.
3. In the same file, uncomment `demo-daily-reminder-2min` (2-minute schedule).
4. Restart these processes from the `backend` folder:
	- `python run.py`
	- `python -m celery -A celery_worker.celery worker --loglevel=info --pool=solo`
	- `python -m celery -A celery_beat.celery beat --loglevel=info`
5. After demo, switch back by re-enabling `daily-reminder-placeholder`, re-commenting `demo-daily-reminder-2min`, and restarting Celery beat.
