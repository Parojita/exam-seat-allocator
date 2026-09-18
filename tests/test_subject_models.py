import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Branch, Subject


def test_subject_belongs_to_branch_and_stores_exam_details():
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
            exam_type="Laboratory",
            duration_minutes=120,
            active=True,
        )

        db.session.add(subject)
        db.session.commit()

        saved_subject = db.session.get(Subject, subject.id)

        assert saved_subject.subject_code == "SUB001"
        assert saved_subject.name == "Data Structures"
        assert saved_subject.branch.code == "CSE"
        assert saved_subject.semester == 1
        assert saved_subject.exam_type == "Laboratory"
        assert saved_subject.duration_minutes == 120
        assert saved_subject.active is True
def test_subject_code_must_be_unique():
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

        first_subject = Subject(
            subject_code="SUB001",
            name="Data Structures",
            branch=branch,
            semester=1,
            exam_type="Theory",
            duration_minutes=180,
            active=True,
        )

        second_subject = Subject(
            subject_code="SUB001",
            name="Duplicate Data Structures",
            branch=branch,
            semester=1,
            exam_type="Theory",
            duration_minutes=180,
            active=True,
        )

        db.session.add_all([first_subject, second_subject])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()