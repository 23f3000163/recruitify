from pathlib import Path
import os

from dotenv import load_dotenv

# ── Lifecycle Step 1: Load the main .env BEFORE importing any local modules.
# config.py class bodies execute when the module is first imported.  The
# environment must be populated before that import chain fires.
_here = Path(__file__).resolve().parent
load_dotenv(_here / ".env", override=False)

# ── Lifecycle Step 2: Load optional Celery / jobs override AFTER the main .env.
# Check the project-root path first (for IDEs that run from the repo root), then
# fall back to the sibling path (for direct execution from backend/).
_jobs_env_from_root = Path("backend/.env.jobs.local")
if _jobs_env_from_root.exists():
    load_dotenv(_jobs_env_from_root, override=False)
else:
    _jobs_env_from_backend = _here / ".env.jobs.local"
    if _jobs_env_from_backend.exists():
        load_dotenv(_jobs_env_from_backend, override=False)

# ── Lifecycle Step 3: Now safe to import local application modules.
from app import create_app  # noqa: E402


# Create Flask app using factory
app = create_app()


if __name__ == "__main__":
    # Run configuration (can be overridden using environment variables)
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    app.run(host=host, port=port, debug=debug)