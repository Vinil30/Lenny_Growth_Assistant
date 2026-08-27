from flask import Flask, render_template, jsonify
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


app = create_app()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
