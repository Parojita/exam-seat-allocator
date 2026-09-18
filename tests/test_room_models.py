import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import Room, Seat


def test_room_stores_desk_matrix_information():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        room = Room(
            room_number="101",
            rows=5,
            columns=4,
            students_per_desk=1,
        )

        db.session.add(room)
        db.session.commit()

        saved_room = db.session.get(Room, room.id)

        assert saved_room.room_number == "101"
        assert saved_room.rows == 5
        assert saved_room.columns == 4
        assert saved_room.students_per_desk == 1
        assert saved_room.capacity == 20


def test_room_number_must_be_unique():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        first_room = Room(
            room_number="101",
            rows=5,
            columns=4,
            students_per_desk=1,
        )

        second_room = Room(
            room_number="101",
            rows=6,
            columns=5,
            students_per_desk=1,
        )

        db.session.add_all([first_room, second_room])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_seat_stores_imported_layout_information():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        room = Room(
            room_number="101",
            rows=5,
            columns=4,
            students_per_desk=2,
        )

        seat = Seat(
            room=room,
            desk_code="D01",
            seat_code="S01A",
            row_code="R01",
            column_code="C01",
            accessible=True,
            active=True,
        )

        db.session.add(seat)
        db.session.commit()

        saved_seat = db.session.get(Seat, seat.id)

        assert saved_seat.room.room_number == "101"
        assert saved_seat.desk_code == "D01"
        assert saved_seat.seat_code == "S01A"
        assert saved_seat.row_code == "R01"
        assert saved_seat.column_code == "C01"
        assert saved_seat.accessible is True
        assert saved_seat.active is True
        assert saved_seat.label == "S01A"


def test_seat_code_must_be_unique_within_room():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        room = Room(
            room_number="101",
            rows=5,
            columns=4,
            students_per_desk=2,
        )

        first_seat = Seat(
            room=room,
            desk_code="D01",
            seat_code="S01A",
            row_code="R01",
            column_code="C01",
            accessible=False,
            active=True,
        )

        duplicate_seat = Seat(
            room=room,
            desk_code="D02",
            seat_code="S01A",
            row_code="R01",
            column_code="C02",
            accessible=False,
            active=True,
        )

        db.session.add_all([first_seat, duplicate_seat])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()