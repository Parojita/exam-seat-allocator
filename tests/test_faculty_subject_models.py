import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Branch, Faculty, FacultySubject, Subject


def test_faculty_subject_links_faculty_to_subject():
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

        subject = Subject(
            subject_code="SUB001",
            name="Data Structures",
            branch=branch,
            semester=1,
            exam_type="Theory",
            duration_minutes=180,
            active=True,
        )

        faculty = Faculty(
            faculty_id="FAC001",
            name="Ananya Sen",
            department="CSE",
            email="ananya.sen@example.edu",
            max_duties=5,
        )

        faculty_subject = FacultySubject(
            faculty=faculty,
            subject=subject,
        )

        db.session.add(faculty_subject)
        db.session.commit()

        saved_record = db.session.get(
            FacultySubject,
            faculty_subject.id,
        )

        assert saved_record.faculty.faculty_id == "FAC001"
        assert saved_record.subject.subject_code == "SUB001"
def test_faculty_subject_pair_must_be_unique():
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

        subject = Subject(
            subject_code="SUB001",
            name="Data Structures",
            branch=branch,
            semester=1,
            exam_type="Theory",
            duration_minutes=180,
            active=True,
        )

        faculty = Faculty(
            faculty_id="FAC001",
            name="Ananya Sen",
            department="CSE",
            email="ananya.sen@example.edu",
            max_duties=5,
        )

        first_record = FacultySubject(
            faculty=faculty,
            subject=subject,
        )

        duplicate_record = FacultySubject(
            faculty=faculty,
            subject=subject,
        )

        db.session.add_all(
            [first_record, duplicate_record]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()