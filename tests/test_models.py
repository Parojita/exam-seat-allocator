import pytest
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Branch, Student


def test_student_belongs_to_branch():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        branch = Branch(name="Computer Science")
        student = Student(
            roll_number="CSE001",
            name="Test Student",
            branch=branch,
        )

        db.session.add(student)
        db.session.commit()

        saved_student = db.session.get(Student, student.id)

        assert saved_student.name == "Test Student"
        assert saved_student.branch.name == "Computer Science"
def test_student_roll_number_must_be_unique():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()

        branch = Branch(name="Computer Science")

        first_student = Student(
            roll_number="CSE001",
            name="First Student",
            branch=branch,
        )

        second_student = Student(
            roll_number="CSE001",
            name="Second Student",
            branch=branch,
        )

        db.session.add_all([first_student, second_student])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()