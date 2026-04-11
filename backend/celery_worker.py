"""Celery worker entrypoint.

Run:
    celery -A celery_worker.celery worker --loglevel=info
"""

from pathlib import Path

from dotenv import load_dotenv

from app import create_app
from app.jobs.celery_app import init_celery


_jobs_env_from_root = Path("backend/.env.jobs.local")
if _jobs_env_from_root.exists():
    load_dotenv("backend/.env.jobs.local", override=False)
else:
    _jobs_env_from_backend = Path(__file__).resolve().with_name(".env.jobs.local")
    if _jobs_env_from_backend.exists():
        load_dotenv(_jobs_env_from_backend, override=False)

flask_app = create_app()
celery = init_celery(flask_app)
