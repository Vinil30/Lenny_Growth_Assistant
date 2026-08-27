from .artifacts import artifacts_bp
from .chat import chat_bp
from .health import health_bp
from .sessions import sessions_bp


def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(artifacts_bp, url_prefix="/api/artifacts")
