import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import Branch, Examination, Subject


def test_examination_stores_schedule_and_subject():
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

        examination = Examination(
            exam_code="EXAM001",
            subject=subject,
            exam_date=date(2026, 10, 15),
            start_time=time(10, 0),
            end_time=time(13, 0),
            exam_type="Theory",
        )

        db.session.add(examination)
        db.session.commit()

        saved_examination = db.session.get(
            Examination,
            examination.id,
        )

        assert saved_examination.exam_code == "EXAM001"
        assert saved_examination.subject.subject_code == "SUB001"
        assert saved_examination.exam_date == date(2026, 10, 15)
        assert saved_examination.start_time == time(10, 0)
        assert saved_examination.end_time == time(13, 0)
        assert saved_examination.exam_type == "Theory"
def test_exam_code_must_be_unique():
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

        first_examination = Examination(
            exam_code="EXAM001",
            subject=subject,
            exam_date=date(2026, 10, 15),
            start_time=time(10, 0),
            end_time=time(13, 0),
            exam_type="Theory",
        )

        duplicate_examination = Examination(
            exam_code="EXAM001",
            subject=subject,
            exam_date=date(2026, 10, 16),
            start_time=time(10, 0),
            end_time=time(13, 0),
            exam_type="Theory",
        )

        db.session.add_all(
            [first_examination, duplicate_examination]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()