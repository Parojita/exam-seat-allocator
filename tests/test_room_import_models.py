from app import create_app
from app.extensions import db
from app.models import Room


def test_room_stores_imported_capacity_information():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        room = Room(
            room_number="B1-101",
            building="Building 1",
            floor=1,
            official_capacity=60,
            exam_capacity=50,
            room_type="Theory",
        )

        db.session.add(room)
        db.session.commit()

        saved_room = db.session.get(Room, room.id)

        assert saved_room.room_number == "B1-101"
        assert saved_room.building == "Building 1"
        assert saved_room.floor == 1
        assert saved_room.official_capacity == 60
        assert saved_room.exam_capacity == 50
        assert saved_room.room_type == "Theory"
        assert saved_room.capacity == 50