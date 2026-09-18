from app import create_app
from app.extensions import db
from app.models import Branch, Student


def test_student_stores_imported_information():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        branch = Branch(
            code="CSE",
            name="Computer Science and Engineering",
        )

        student = Student(
            roll_number="CSE001",
            name="Aarav Sharma",
            branch=branch,
            semester=6,
            email="aarav.sharma@example.edu",
            photo_path="photos/CSE001.jpg",
            special_request="Wheelchair accessible seat",
            rfid_uid=None,
            active=True,
        )

        db.session.add(student)
        db.session.commit()

        saved_student = db.session.get(Student, student.id)

        assert saved_student.roll_number == "CSE001"
        assert saved_student.name == "Aarav Sharma"
        assert saved_student.branch.code == "CSE"
        assert saved_student.semester == 6
        assert saved_student.email == "aarav.sharma@example.edu"
        assert saved_student.photo_path == "photos/CSE001.jpg"
        assert (
            saved_student.special_request
            == "Wheelchair accessible seat"
        )
        assert saved_student.rfid_uid is None
        assert saved_student.active is True