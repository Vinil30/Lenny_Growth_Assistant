from flask import Blueprint, jsonify, request
from models import db
from models.database import ChatSession
from services.chat import ChatService


sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.post("")
def create_session():
    service = ChatService()
    session = service.create_session((request.get_json(silent=True) or {}).get("user_metadata", {}))
    return jsonify({"id": session.id, "title": session.title, "provider": session.provider}), 201


@sessions_bp.get("")
def list_sessions():
    sessions = ChatSession.query.order_by(ChatSession.updated_at.desc()).limit(50).all()
    return jsonify(
        [{"id": s.id, "title": s.title, "provider": s.provider, "updated_at": s.updated_at.isoformat()} for s in sessions]
    )


@sessions_bp.get("/<session_id>")
def get_session(session_id):
    history = ChatService().get_history(session_id)
    if history is None:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({"id": session_id, "messages": history})


@sessions_bp.delete("/<session_id>")
def delete_session(session_id):
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    db.session.delete(session)
    db.session.commit()
    return jsonify({"ok": True})
