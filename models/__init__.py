from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


from .database import Artifact, ChatMessage, ChatSession  # noqa: E402,F401
