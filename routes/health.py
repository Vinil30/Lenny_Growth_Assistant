from flask import Blueprint, jsonify
from sqlalchemy import text
from models import db
from utils.config import settings


health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health():
    db_ok = True
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return jsonify({"ok": db_ok, "provider": settings.llm_provider, "rag_data_dir": settings.rag_data_dir})
