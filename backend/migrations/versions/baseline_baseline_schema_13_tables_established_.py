"""baseline schema - 13 tables established via create_db.py

Revision ID: baseline
Revises:
Create Date: 2026-07-03 16:43:00.384751

This is the root migration revision for Recruitify.

Strategy
--------
The 13 database tables were created by `create_db.py` (which calls
`db.create_all()`) before Flask-Migrate was introduced.  This revision
exists as the Alembic baseline so that all future schema changes can be
tracked as migrations on top of it.

upgrade() and downgrade() are intentionally empty because:

  - For EXISTING databases: the tables already exist.  The existing database
    is stamped at this revision via `flask db stamp head`, which writes
    "baseline" into the `alembic_version` table without touching the schema.

  - For NEW databases: `create_db.py` creates all tables via `db.create_all()`
    and then calls `flask_migrate.stamp()` which also stamps "baseline".
    `flask db upgrade` then applies only migrations AFTER this revision.

All future schema changes MUST be made through Alembic migrations:
  flask --app run:app db migrate -m "describe the change"
  flask --app run:app db upgrade
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Schema already established by create_db.py / db.create_all().
    # See module docstring for full explanation.
    pass


def downgrade():
    # Intentionally empty — dropping the initial schema requires a full
    # database reset, which is out of scope for a migration downgrade.
    pass
