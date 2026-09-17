from app import create_app
from app.extensions import db


def test_homepage_returns_success():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Examination Seat Allocator" in response.data


def test_database_uses_test_configuration():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        assert db.engine.url.database == ":memory:"