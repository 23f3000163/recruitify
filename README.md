# Recruitify

## Project overview

Recruitify is a full-stack placement portal for students, companies, and administrators. It supports placement drives, applications, interviews, offers, role-based JWT authorization, and background automation such as reminders, reports, and exports.

## Tech stack

| Area | Technology |
| --- | --- |
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Migrate/Alembic |
| Authentication | Flask-JWT-Extended |
| Development database | SQLite |
| Production database | PostgreSQL |
| Background work | Celery and Redis |
| Frontend | Vue 3, Vite, Axios, Vue Router |
| Testing | pytest and Vitest |

## Project structure

```text
recruitify/
├── backend/
│   ├── app/                 # App factory, models, blueprints, and services
│   ├── migrations/          # Versioned Alembic migrations
│   ├── scripts/             # Developer utilities such as admin seeding
│   ├── create_db.py         # New local SQLite bootstrap only
│   ├── run.py               # Flask entry point
│   └── requirements.txt
├── frontend/
│   ├── src/                 # Vue application source
│   └── package.json
├── CONTRIBUTING.md
└── README.md
```

## Local developer setup

Prerequisites: Python 3, Node.js/npm, and Redis when exercising background jobs or Redis-backed caching.

1. Clone and enter the repository.

   ```bash
   git clone <repository-url>
   cd recruitify
   ```

2. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, use `.venv\Scripts\Activate.ps1`.

3. Install backend dependencies.

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Configure environment variables. The development defaults work with local SQLite, but secrets and admin credentials should be overridden; see [Environment variables](#environment-variables).

5. Create a brand-new local database, then seed an administrator.

   ```bash
   cd backend
   python create_db.py
   python scripts/seed_admin.py
   ```

6. Start the backend from `backend/`.

   ```bash
   python run.py
   ```

7. In another terminal, install and start the frontend.

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The API defaults to `http://127.0.0.1:5000`; Vite prints the frontend URL, normally `http://localhost:5173`.

## Backend setup

Run backend and migration commands from `backend/` with the repository virtual environment active. `run.py` constructs the application through `create_app()`, and the health check is available at `GET /health`.

```bash
cd backend
python run.py
```

The API binds to `127.0.0.1:5000` by default. Set `FLASK_RUN_HOST`, `FLASK_RUN_PORT`, or `FLASK_DEBUG` to override those development values.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` when the API is not at `http://127.0.0.1:5000`. Create a production bundle with `npm run build`.

## Environment variables

Environment variables may be exported in the shell or placed in a local, ignored `.env` file appropriate to the process. Never commit secrets.

| Variable | Purpose | Development default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection URL | `sqlite:///backend/instance/recruitify.db` (resolved by Flask) |
| `SECRET_KEY` | Flask signing secret | Development-only fallback |
| `JWT_SECRET_KEY` | JWT signing secret | Development-only fallback |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173` |
| `REDIS_URL` | Shared Redis base URL | `redis://127.0.0.1:6379/0` |
| `CELERY_BROKER_URL` | Celery broker override | Derived from `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Celery result backend override | Redis database 1 |
| `DEFAULT_ADMIN_USERNAME` | Seeded admin username | `admin` |
| `DEFAULT_ADMIN_EMAIL` | Seeded admin email | Development fallback |
| `DEFAULT_ADMIN_PASSWORD` | Seeded admin password | Development fallback; override it |
| `DEFAULT_ADMIN_DESIGNATION` | Seeded admin designation | `Super Admin` |
| `VITE_API_BASE_URL` | Frontend API base URL | `http://127.0.0.1:5000` |

Production must set strong, distinct secrets and an explicit PostgreSQL `DATABASE_URL`, for example `postgresql+psycopg2://user:password@host:5432/recruitify`. Job schedules, mail delivery, caching, and export behavior have additional settings in `backend/app/__init__.py`.

## Database strategy

Recruitify uses SQLite for development and PostgreSQL for production.

- **SQLite in development** gives contributors a zero-configuration database in a single ignored local file. This makes onboarding, feature work, and disposable local testing fast.
- **PostgreSQL in production** provides stronger concurrency, operational tooling, integrity, and reliability for multi-user placement workflows and future growth.
- **SQLAlchemy** keeps queries and business logic largely database-agnostic, while migrations make database-specific schema changes explicit and reviewable.
- **Flask-Migrate/Alembic** gives Recruitify a scalable, portfolio-quality schema history rather than relying on ad hoc table creation or manual production edits.

SQLite and PostgreSQL are not identical. Review and test generated migrations locally, and validate them against PostgreSQL before production deployment when they use database-specific types, constraints, or SQL.

## Local development workflow

For an existing checkout:

1. Pull the latest code and activate the virtual environment.
2. Install changed Python and Node dependencies.
3. From `backend/`, run `flask --app run:app db upgrade` against the existing local database.
4. Start the backend and frontend.
5. Start Redis, a Celery worker, and Celery beat only when developing background jobs.
6. Run the relevant tests before opening a pull request.

Do not rerun `create_db.py` to update an existing database; migrations own all ongoing schema evolution.

## Database migration workflow

When a model change requires a schema change:

```text
Edit backend/app/models.py
            ↓
Generate a migration
            ↓
Review upgrade() and downgrade()
            ↓
Apply and test the migration locally
            ↓
Commit the model and migration together
```

Run these commands from `backend/`:

```bash
flask --app run:app db migrate -m "describe the schema change"
# Inspect migrations/versions/<revision>_*.py before continuing.
flask --app run:app db upgrade
flask --app run:app db current
```

Autogeneration is a draft, not proof that a migration is correct. Check constraints, defaults, data transformations, and both `upgrade()` and `downgrade()`.

Migration files must be committed because they are the ordered, reproducible instructions that move every developer, CI, staging, and production database to the same schema. Commit the model change and its migration together so code and schema cannot drift apart.

Never edit or delete an old migration after it has been shared. Other databases may already identify that revision as applied; rewriting it makes history inconsistent. Correct a shared migration with a new migration. If parallel branches generate conflicting heads, coordinate and create an Alembic merge revision rather than rewriting either branch's history.

## Fresh local database setup

`backend/create_db.py` is a bootstrap utility **only for a brand-new local SQLite database**. It creates tables from the current SQLAlchemy metadata and stamps the database at the current migration head (currently the baseline), allowing later migrations to continue from a known revision.

Use it for first-time local setup or after intentionally deleting the ignored local SQLite database:

```bash
cd backend
python create_db.py
```

Do **not** use it for:

- an existing database;
- staging or production;
- applying or repairing schema changes.

`db.create_all()` can create missing tables but does not version, alter, or safely reproduce an evolving schema. Recruitify therefore limits it to this local bootstrap. After a database exists, use `flask --app run:app db upgrade` for every schema change.

## Production deployment notes

Production should use PostgreSQL by setting `DATABASE_URL`; SQLite is intended for local development only. SQLAlchemy keeps application business logic mostly independent of the database engine, while Alembic records the schema operations each environment must apply.

A typical release sequence is:

1. Back up the production database and verify the restore procedure.
2. Deploy code containing both model changes and reviewed migration files.
3. Run `flask --app run:app db upgrade` as a controlled release step, once per environment.
4. Verify `flask --app run:app db current` and application health.
5. Start or restart the API, Celery worker, and Celery beat using the platform's process manager.

Never run `create_db.py`, `db.create_all()`, or manual DDL against production. Review potentially locking or destructive migrations and plan a rollback before deployment. Keep secrets outside source control and restrict database credentials to the permissions the application and migration job require.

## Background jobs runbook

Redis, a Celery worker, and Celery beat are needed for reminders, monthly reports, exports, and other asynchronous jobs.

```bash
docker run -d --name recruitify-redis -p 6379:6379 redis:7-alpine

# Run each command from backend/ in a separate terminal.
python run.py
python -m celery -A celery_worker.celery worker --loglevel=info
python -m celery -A celery_beat.celery beat --loglevel=info
```

On Windows, the worker may require `--pool=solo`. Check queue health with `GET /jobs/health`, then exercise interview reminders, monthly admin/company reports, or student/company exports.

For a short demo schedule, edit `beat_schedule` in `backend/app/jobs/celery_app.py`: disable `daily-reminder-placeholder`, enable `demo-daily-reminder-2min`, and restart Celery beat. Restore the daily schedule after the demo.

## Common development commands

Unless noted otherwise, backend commands run from `backend/` and frontend commands from `frontend/`.

| Task | Command | What it does |
| --- | --- | --- |
| Start backend | `python run.py` | Runs the Flask development server. |
| Start frontend | `npm run dev` | Runs the Vite development server. |
| Build frontend | `npm run build` | Creates the production frontend bundle. |
| Create fresh local database | `python create_db.py` | Bootstraps and stamps a new local SQLite database only. |
| Show current migration | `flask --app run:app db current` | Displays the revision applied to the configured database. |
| Show migration history | `flask --app run:app db history` | Lists known revisions in order. |
| Generate migration | `flask --app run:app db migrate -m "message"` | Autogenerates a migration draft from model metadata. |
| Upgrade database | `flask --app run:app db upgrade` | Applies pending migrations. |
| Downgrade one revision | `flask --app run:app db downgrade -1` | Reverts one migration; review data-loss risk first. |
| Seed admin | `python scripts/seed_admin.py` | Ensures the configured admin user and profile exist. |
| Run backend tests | `pytest` | Runs discovered pytest tests (when present). |
| Run frontend tests | `npm test` | Runs the Vitest suite once. |
| Start Celery worker | `python -m celery -A celery_worker.celery worker --loglevel=info` | Processes queued background tasks. |
| Start Celery beat | `python -m celery -A celery_beat.celery beat --loglevel=info` | Dispatches scheduled tasks. |

## Best practices

- Always review autogenerated migrations before applying them.
- Commit model changes and their migration files together.
- Never edit a committed, shared migration; add a corrective migration.
- Never alter a production schema manually.
- Never use `create_db.py` for schema updates.
- Test upgrades locally and validate PostgreSQL-sensitive changes before deployment.
- Confirm the active `DATABASE_URL` before migration or seed commands.
- Back up production data and understand downgrade/data-loss behavior before release.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Migration is already applied | Run `flask --app run:app db current` and `db history`. If the expected revision is current, do not reapply it. Never delete the version row to force a rerun. |
| Database schema is out of sync | Back up the database, compare `db current` with `db heads`, and apply pending migrations with `db upgrade`. If tables were changed manually, create a reviewed reconciliation migration instead of guessing or rerunning `create_db.py`. |
| `alembic_version` table is missing | For a truly new local SQLite database, use `python create_db.py`. For an existing database, verify its schema matches the baseline before using `flask --app run:app db stamp baseline`; stamping records history but applies no schema. Back up first. |
| Migration conflict or multiple heads | Pull all migration files, run `flask --app run:app db heads`, coordinate with the other author, and create a merge revision with `flask --app run:app db merge <head1> <head2> -m "merge heads"`. |
| Database connection fails | Check `DATABASE_URL`, credentials, host, port, database existence, driver installation, and network access. Confirm which environment file the process loads. |
| Migration command cannot find the app | Run it from `backend/` with the virtual environment active and include `--app run:app`. |
| SQLite reports a locked database | Stop duplicate backend or shell processes using the file, then retry. Do not delete the database unless its data is disposable. |

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes.

brew services stop redis
brew services start redis
brew services restart redis
brew services list
redis-cli ping