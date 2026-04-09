import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import ActivityLog, db


LEGACY_ACTION_NAME = "Application Updated"


def cleanup_legacy_activity_logs(apply_changes=False):
    app = create_app()

    with app.app_context():
        query = ActivityLog.query.filter(ActivityLog.action == LEGACY_ACTION_NAME)
        rows_to_delete = query.count()

        print(f"[INFO] Legacy audit rows matched: {rows_to_delete}")

        if not apply_changes:
            print("[DRY-RUN] No rows deleted. Re-run with --apply to permanently delete.")
            return 0

        if rows_to_delete == 0:
            print("[OK] Nothing to delete.")
            return 0

        try:
            deleted_count = query.delete(synchronize_session=False)
            db.session.commit()
            print(f"[OK] Deleted {deleted_count} legacy activity rows.")
            return deleted_count
        except Exception as exc:
            db.session.rollback()
            print(f"[ERROR] Cleanup failed: {exc}")
            return -1


def main():
    parser = argparse.ArgumentParser(
        description="One-time cleanup for legacy admin activity logs."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Permanently delete matched rows. Without this flag, script runs in dry-run mode.",
    )
    args = parser.parse_args()

    cleanup_legacy_activity_logs(apply_changes=args.apply)


if __name__ == "__main__":
    main()