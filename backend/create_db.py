"""Bootstrap utility for a brand-new local SQLite database.

Purpose
-------
This script is intended ONLY for setting up a developer's local SQLite
database from scratch.  It combines two steps:

  1. Creates all tables from the current SQLAlchemy model definitions.
  2. Stamps the database at the current Flask-Migrate revision head so that
     `flask db upgrade` works correctly for all future schema changes.

When to use
-----------
  - First-time local setup on a new machine.
  - After deleting the local `instance/recruitify.db` file to start fresh.

When NOT to use
---------------
  - To apply schema changes to an EXISTING database (use `flask db upgrade`).
  - In any CI, staging, or production environment (use `flask db upgrade`).

For all schema changes after initial setup
-------------------------------------------
  flask --app run:app db migrate -m "describe the change"
  # review the generated migration file
  flask --app run:app db upgrade
"""

from pathlib import Path

from dotenv import load_dotenv

# Load the main .env BEFORE importing any local application modules so that
# config.py class bodies find the environment populated when they execute.
_here = Path(__file__).resolve().parent
load_dotenv(_here / ".env", override=False)

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402
from flask_migrate import stamp  # noqa: E402


def bootstrap():
    """Create all tables and stamp the migration baseline."""
    app = create_app()

    with app.app_context():
        # Import models so SQLAlchemy metadata is fully populated before
        # create_all() is called.  This mirrors the import in create_app()
        # but is made explicit here for clarity.
        from app import models  # noqa: F401

        db.create_all()
        print("✅ Database tables created successfully.")

        # Stamp the database at the current migration head.  This writes the
        # current Alembic revision into the `alembic_version` table without
        # running any migration scripts.  It tells Flask-Migrate that this
        # database is already at the baseline state and that `flask db upgrade`
        # should only apply future migrations beyond this point.
        stamp()
        print("✅ Database stamped at current migration head.")
        print()
        print("Database is ready.  For future schema changes, use:")
        print("  flask --app run:app db migrate -m \"describe the change\"")
        print("  flask --app run:app db upgrade")


if __name__ == "__main__":
    bootstrap()