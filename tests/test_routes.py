from pathlib import Path
from uuid import uuid4

from app import create_app, _ensure_sqlite_parent, _normalize_sqlite_database_url
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


def test_file_sqlite_parent_is_created():
    database_path = Path(".pytest-tmp") / str(uuid4()) / "nested" / "app.db"
    database_url = _normalize_sqlite_database_url(f"sqlite:///{database_path.as_posix()}", str(Path.cwd()))
    _ensure_sqlite_parent(database_url)
    assert database_path.parent.is_dir()


def test_file_sqlite_sessions_work():
    database_path = Path(".pytest-tmp") / str(uuid4()) / "app.db"
    app = create_app(
        {
            "TESTING": True,
            "AUTO_CREATE_DB": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
        }
    )
    res = app.test_client().get("/api/sessions")
    assert res.status_code == 200
    assert database_path.is_file()


def test_static_assets_are_not_empty():
    assert Path("static/js/app.js").stat().st_size > 0
    assert Path("static/css/app.css").stat().st_size > 0
