import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Faculty, FacultyAvailability


def test_faculty_availability_stores_date_and_session():
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

        availability = FacultyAvailability(
            faculty=faculty,
            date=date(2026, 10, 15),
            session="Morning",
            available=True,
        )

        db.session.add(availability)
        db.session.commit()

        saved_availability = db.session.get(
            FacultyAvailability,
            availability.id,
        )

        assert saved_availability.faculty.faculty_id == "FAC001"
        assert saved_availability.date == date(2026, 10, 15)
        assert saved_availability.session == "Morning"
        assert saved_availability.available is True
def test_faculty_date_session_availability_must_be_unique():
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

        first_availability = FacultyAvailability(
            faculty=faculty,
            date=date(2026, 10, 15),
            session="Morning",
            available=True,
        )

        duplicate_availability = FacultyAvailability(
            faculty=faculty,
            date=date(2026, 10, 15),
            session="Morning",
            available=False,
        )

        db.session.add_all(
            [first_availability, duplicate_availability]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()