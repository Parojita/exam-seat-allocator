from app import create_app


def test_homepage_returns_success():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Examination Seat Allocator" in response.data