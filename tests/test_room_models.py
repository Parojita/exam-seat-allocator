import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Room


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