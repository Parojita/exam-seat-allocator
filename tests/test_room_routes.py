from app import create_app
from app.extensions import db
from app.models import Room, Seat


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()

    return app


def test_admin_rooms_page_returns_success():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/admin/rooms")

    assert response.status_code == 200
    assert b"Room Management" in response.data
    assert b"Add Examination Room" in response.data


def test_admin_rooms_creates_room_and_seats():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/rooms",
        data={
            "room_number": "A101",
            "building": "Academic Block",
            "floor": "1",
            "room_type": "Classroom",
            "rows": "2",
            "columns": "3",
        },
    )

    assert response.status_code == 200
    assert b"Room A101 created with 6 seats." in response.data

    with app.app_context():
        room = db.session.scalar(
            db.select(Room).where(
                Room.room_number == "A101"
            )
        )

        assert room is not None
        assert room.building == "Academic Block"
        assert room.floor == 1
        assert room.room_type == "Classroom"
        assert room.rows == 2
        assert room.columns == 3
        assert room.students_per_desk == 1
        assert room.exam_capacity == 6
        assert room.capacity == 6

        seats = db.session.execute(
            db.select(Seat)
            .where(Seat.room_id == room.id)
            .order_by(Seat.id)
        ).scalars().all()

        assert len(seats) == 6

        assert [
            seat.seat_code
            for seat in seats
        ] == [
            "A1",
            "A2",
            "A3",
            "B1",
            "B2",
            "B3",
        ]

        assert all(
            seat.active is True
            for seat in seats
        )

        assert all(
            seat.accessible is False
            for seat in seats
        )


def test_admin_rooms_rejects_duplicate_room_number():
    app = create_test_app()
    client = app.test_client()

    first_response = client.post(
        "/admin/rooms",
        data={
            "room_number": "A101",
            "rows": "2",
            "columns": "3",
        },
    )

    second_response = client.post(
        "/admin/rooms",
        data={
            "room_number": "a101",
            "rows": "3",
            "columns": "4",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        b"A room with this room number already exists."
        in second_response.data
    )

    with app.app_context():
        room_count = db.session.scalar(
            db.select(
                db.func.count(Room.id)
            )
        )

        seat_count = db.session.scalar(
            db.select(
                db.func.count(Seat.id)
            )
        )

        assert room_count == 1
        assert seat_count == 6


def test_admin_rooms_rejects_invalid_dimensions():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/rooms",
        data={
            "room_number": "A102",
            "rows": "0",
            "columns": "5",
        },
    )

    assert response.status_code == 200
    assert (
        b"Rows must be between 1 and 26."
        in response.data
    )

    with app.app_context():
        room_count = db.session.scalar(
            db.select(
                db.func.count(Room.id)
            )
        )

        seat_count = db.session.scalar(
            db.select(
                db.func.count(Seat.id)
            )
        )

        assert room_count == 0
        assert seat_count == 0
def test_navigation_contains_room_management_link():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/admin/import")

    assert response.status_code == 200
    assert b'href="/admin/rooms"' in response.data
    assert b"Room Management" in response.data


def test_admin_rooms_requires_room_number():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/rooms",
        data={
            "room_number": "",
            "rows": "5",
            "columns": "10",
        },
    )

    assert response.status_code == 200
    assert b"Room number is required." in response.data

    with app.app_context():
        assert db.session.scalar(
            db.select(db.func.count(Room.id))
        ) == 0

        assert db.session.scalar(
            db.select(db.func.count(Seat.id))
        ) == 0


def test_admin_rooms_rejects_invalid_columns():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/rooms",
        data={
            "room_number": "A103",
            "rows": "5",
            "columns": "101",
        },
    )

    assert response.status_code == 200
    assert (
        b"Columns must be between 1 and 100."
        in response.data
    )

    with app.app_context():
        assert db.session.scalar(
            db.select(db.func.count(Room.id))
        ) == 0


def test_admin_rooms_rejects_invalid_floor():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/rooms",
        data={
            "room_number": "A104",
            "floor": "first",
            "rows": "5",
            "columns": "10",
        },
    )

    assert response.status_code == 200
    assert (
        b"Floor must be a whole number."
        in response.data
    )

    with app.app_context():
        assert db.session.scalar(
            db.select(db.func.count(Room.id))
        ) == 0