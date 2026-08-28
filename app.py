from flask import Flask, render_template, jsonify
from pathlib import Path
from sqlalchemy.engine import make_url
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
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_sqlite_database_url(
        app.config["SQLALCHEMY_DATABASE_URI"], app.root_path
    )
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"connect_timeout": settings.db_connect_timeout_seconds}
        }
    _ensure_sqlite_parent(app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)
    register_routes(app)
    _install_db_initializer(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/<path:path>")
    def browser_fallback(path):
        if path.startswith("api/"):
            return jsonify({"error": "Not found."}), 404
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found."}), 404

    if app.config.get("AUTO_CREATE_DB", settings.auto_create_db):
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                app.logger.exception("Database initialization failed during startup.")
    return app


def _normalize_sqlite_database_url(database_url: str, base_path: str) -> str:
    try:
        url = make_url(database_url)
    except Exception:
        return database_url
    if url.drivername.split("+", 1)[0] != "sqlite":
        return database_url
    raw_path = url.database
    if not raw_path or raw_path == ":memory:":
        return database_url
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(base_path) / path
    return f"sqlite:///{path.as_posix()}"


def _ensure_sqlite_parent(database_url: str) -> None:
    try:
        url = make_url(database_url)
    except Exception:
        return
    if url.drivername.split("+", 1)[0] != "sqlite":
        return
    raw_path = url.database
    if not raw_path or raw_path == ":memory:":
        return
    Path(raw_path).parent.mkdir(parents=True, exist_ok=True)


def _install_db_initializer(app):
    state = {"done": False}

    @app.before_request
    def ensure_db_ready():
        if state["done"] or not app.config.get("AUTO_CREATE_DB", settings.auto_create_db):
            return
        try:
            db.create_all()
            state["done"] = True
        except Exception:
            app.logger.exception("Database initialization failed before request.")
            state["done"] = False


app = create_app()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
