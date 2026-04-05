"""Celery worker entrypoint.

Run:
    celery -A celery_worker.celery worker --loglevel=info
"""

from app import create_app
from app.jobs.celery_app import init_celery

flask_app = create_app()
celery = init_celery(flask_app)
