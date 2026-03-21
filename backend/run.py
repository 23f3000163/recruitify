import os
from app import create_app

# Create Flask app using factory
app = create_app("development")


if __name__ == "__main__":
    # Run configuration (can be overridden using environment variables)
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    app.run(host=host, port=port, debug=debug)