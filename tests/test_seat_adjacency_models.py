import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import Room, Seat, SeatAdjacency


def test_seat_adjacency_links_two_seats():
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

        second_seat = Seat(
            room=room,
            desk_code="D01",
            seat_code="S01B",
            row_code="R01",
            column_code="C01",
            accessible=False,
            active=True,
        )

        adjacency = SeatAdjacency(
            seat=first_seat,
            adjacent_seat=second_seat,
        )

        db.session.add(adjacency)
        db.session.commit()

        saved_adjacency = db.session.get(
            SeatAdjacency,
            adjacency.id,
        )

        assert saved_adjacency.seat.seat_code == "S01A"
        assert saved_adjacency.adjacent_seat.seat_code == "S01B"
        assert saved_adjacency.seat.room.room_number == "101"
        assert saved_adjacency.adjacent_seat.room.room_number == "101"


def test_same_adjacency_pair_must_be_unique():
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

        second_seat = Seat(
            room=room,
            desk_code="D01",
            seat_code="S01B",
            row_code="R01",
            column_code="C01",
            accessible=False,
            active=True,
        )

        first_adjacency = SeatAdjacency(
            seat=first_seat,
            adjacent_seat=second_seat,
        )

        duplicate_adjacency = SeatAdjacency(
            seat=first_seat,
            adjacent_seat=second_seat,
        )

        db.session.add_all(
            [first_adjacency, duplicate_adjacency]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()