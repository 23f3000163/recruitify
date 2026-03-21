from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Import models so SQLAlchemy knows them
    from app import models  # important

    db.create_all()
    print("✅ Database tables created successfully!")