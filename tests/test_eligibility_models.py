import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Branch, Student, StudentEligibility, Subject


def test_student_eligibility_links_student_to_subject():
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
            name="Test Student",
            branch=branch,
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

        eligibility = StudentEligibility(
            student=student,
            subject=subject,
            eligible=True,
        )

        db.session.add(eligibility)
        db.session.commit()

        saved_eligibility = db.session.get(
            StudentEligibility,
            eligibility.id,
        )

        assert saved_eligibility.student.roll_number == "CSE001"
        assert saved_eligibility.subject.subject_code == "SUB001"
        assert saved_eligibility.eligible is True
def test_student_subject_eligibility_must_be_unique():
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
            name="Test Student",
            branch=branch,
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

        first_eligibility = StudentEligibility(
            student=student,
            subject=subject,
            eligible=True,
        )

        duplicate_eligibility = StudentEligibility(
            student=student,
            subject=subject,
            eligible=True,
        )

        db.session.add_all(
            [first_eligibility, duplicate_eligibility]
        )

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()