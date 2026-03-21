import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import or_
from app.models import db, User, Admin
from app import create_app


def seed_admin():
    """Ensure a default admin user exists (important)."""

    app = create_app()

    username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@recruitify.com")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    designation = os.getenv("DEFAULT_ADMIN_DESIGNATION", "Super Admin")

    with app.app_context():
        try:
            user = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()

            if not user:
                user = User(
                    username=username,
                    email=email,
                    role="admin",
                    is_active=True
                )
                user.set_password(password)
                db.session.add(user)
                db.session.flush()  # get user_id without commit

            if not user.admin:
                admin_profile = Admin(
                    user_id=user.user_id,
                    designation=designation
                )
                db.session.add(admin_profile)

            db.session.commit()

            print(f"[OK] Admin ensured: username={username}, email={email}")

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to seed admin: {e}")


if __name__ == "__main__":
    seed_admin()