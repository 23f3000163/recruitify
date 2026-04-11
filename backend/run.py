from pathlib import Path
import os

from dotenv import load_dotenv

from app import create_app


_jobs_env_from_root = Path("backend/.env.jobs.local")
if _jobs_env_from_root.exists():
    load_dotenv("backend/.env.jobs.local", override=False)
else:
    _jobs_env_from_backend = Path(__file__).resolve().with_name(".env.jobs.local")
    if _jobs_env_from_backend.exists():
        load_dotenv(_jobs_env_from_backend, override=False)

# Create Flask app using factory
app = create_app()


if __name__ == "__main__":
    # Run configuration (can be overridden using environment variables)
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    app.run(host=host, port=port, debug=debug)