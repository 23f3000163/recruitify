"""Celery worker entrypoint.

Run:
    celery -A celery_worker.celery worker --loglevel=info
"""

from pathlib import Path

from dotenv import load_dotenv

# ── Lifecycle Step 1: Load the main .env BEFORE importing any local modules.
# config.py class bodies execute when the module is first imported.  The
# environment must be populated before that import chain fires.
_here = Path(__file__).resolve().parent
load_dotenv(_here / ".env", override=False)

# ── Lifecycle Step 2: Load optional Celery / jobs override AFTER the main .env.
_jobs_env_from_root = Path("backend/.env.jobs.local")
if _jobs_env_from_root.exists():
    load_dotenv(_jobs_env_from_root, override=False)
else:
    _jobs_env_from_backend = _here / ".env.jobs.local"
    if _jobs_env_from_backend.exists():
        load_dotenv(_jobs_env_from_backend, override=False)

# ── Lifecycle Step 3: Now safe to import local application modules.
from app import create_app  # noqa: E402
from app.jobs.celery_app import init_celery  # noqa: E402


flask_app = create_app()
celery = init_celery(flask_app)
