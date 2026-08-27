from app import create_app
from models import db


def app_client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
    return app.test_client()


def test_health_endpoint():
    client = app_client()
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "provider" in res.get_json()


def test_chat_validation():
    client = app_client()
    res = client.post("/api/chat/message", json={"message": "hello"})
    assert res.status_code == 400
