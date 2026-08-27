from flask import Blueprint, jsonify, request
from services.chat import ChatService
from utils.validation import clean_text, require_json


chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/message")
def message():
    data = request.get_json(silent=True)
    err = require_json(data, ["session_id", "message"])
    if err:
        return jsonify({"error": err}), 400
    try:
        text = clean_text(data["message"])
        result = ChatService().respond(data["session_id"], text)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception:
        return jsonify({"error": "Unexpected server error."}), 500
