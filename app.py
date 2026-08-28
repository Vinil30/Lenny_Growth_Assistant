from flask import Flask, render_template, jsonify
from pathlib import Path
from urllib.parse import urlparse
from models import db
from routes import register_routes
from utils.config import settings
from utils.logging import configure_logging


def create_app(test_config=None):
    configure_logging()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"connect_timeout": settings.db_connect_timeout_seconds}
        }
    _ensure_sqlite_parent(app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)
    register_routes(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found."}), 404

    if app.config.get("AUTO_CREATE_DB", settings.auto_create_db):
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                pass
    return app


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path == ":memory:":
        return
    path = Path(urlparse(raw_path).path or raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)


app = create_app()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
