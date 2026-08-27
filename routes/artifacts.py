from flask import Blueprint, jsonify
from models.database import Artifact


artifacts_bp = Blueprint("artifacts", __name__)


@artifacts_bp.get("/<artifact_id>")
def get_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if not artifact:
        return jsonify({"error": "Artifact not found."}), 404
    return jsonify({"id": artifact.id, "title": artifact.title, "kind": artifact.kind, "content": artifact.content})
