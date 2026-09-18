import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Faculty


def test_faculty_stores_imported_details():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        faculty = Faculty(
            faculty_id="FAC001",
            name="Ananya Sen",
            department="CSE",
            email="ananya.sen@example.edu",
            max_duties=5,
        )

        db.session.add(faculty)
        db.session.commit()

        saved_faculty = db.session.get(
            Faculty,
            faculty.id,
        )

        assert saved_faculty.faculty_id == "FAC001"
        assert saved_faculty.name == "Ananya Sen"
        assert saved_faculty.department == "CSE"
        assert saved_faculty.email == "ananya.sen@example.edu"
        assert saved_faculty.max_duties == 5
def test_faculty_id_must_be_unique():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        first_faculty = Faculty(
            faculty_id="FAC001",
            name="Ananya Sen",
            department="CSE",
            email="ananya.sen@example.edu",
            max_duties=5,
        )

        duplicate_faculty = Faculty(
            faculty_id="FAC001",
            name="Rahul Das",
            department="ECE",
            email="rahul.das@example.edu",
            max_duties=4,
        )

        db.session.add_all(
            [first_faculty, duplicate_faculty]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()