from app import create_app
from models import db
from models.database import ChatMessage


def test_session_isolation_and_persistence():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        c = app.test_client()
        s1 = c.post("/api/sessions", json={}).get_json()["id"]
        s2 = c.post("/api/sessions", json={}).get_json()["id"]
        db.session.add(ChatMessage(session_id=s1, role="user", content="one"))
        db.session.add(ChatMessage(session_id=s2, role="user", content="two"))
        db.session.commit()
        assert c.get(f"/api/sessions/{s1}").get_json()["messages"][0]["content"] == "one"
        assert c.get(f"/api/sessions/{s2}").get_json()["messages"][0]["content"] == "two"


def test_delete_session():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        c = app.test_client()
        session_id = c.post("/api/sessions", json={}).get_json()["id"]
        assert c.delete(f"/api/sessions/{session_id}").status_code == 200
        assert c.get(f"/api/sessions/{session_id}").status_code == 404
