from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import Branch, Examination, Subject


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()

        branch = Branch(
            code="CSE",
            name="Computer Science and Engineering",
        )

        subject = Subject(
            subject_code="CSE301",
            name="Database Systems",
            branch=branch,
            semester=6,
            exam_type="End Semester",
            duration_minutes=180,
            active=True,
        )

        db.session.add(branch)
        db.session.add(subject)
        db.session.commit()

    return app


def get_subject_id(app):
    with app.app_context():
        subject = db.session.scalar(
            db.select(Subject).where(
                Subject.subject_code == "CSE301"
            )
        )

        return subject.id


def valid_examination_data(app):
    return {
        "exam_code": "EXAM-CSE301-2026",
        "subject_id": str(get_subject_id(app)),
        "exam_date": "2026-12-15",
        "start_time": "10:00",
        "end_time": "13:00",
        "exam_type": "End Semester",
    }


def test_admin_examinations_page_returns_success():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/admin/examinations")

    assert response.status_code == 200
    assert b"Examination Management" in response.data
    assert b"Schedule Examination" in response.data
    assert b"CSE301" in response.data


def test_admin_examinations_creates_examination():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/examinations",
        data=valid_examination_data(app),
    )

    assert response.status_code == 200
    assert (
        b"Examination EXAM-CSE301-2026 "
        b"created successfully."
        in response.data
    )

    with app.app_context():
        examination = db.session.scalar(
            db.select(Examination).where(
                Examination.exam_code
                == "EXAM-CSE301-2026"
            )
        )

        assert examination is not None
        assert examination.subject.subject_code == "CSE301"
        assert examination.exam_date == date(2026, 12, 15)
        assert examination.start_time == time(10, 0)
        assert examination.end_time == time(13, 0)
        assert examination.exam_type == "End Semester"


def test_admin_examinations_rejects_duplicate_code():
    app = create_test_app()
    client = app.test_client()

    first_response = client.post(
        "/admin/examinations",
        data=valid_examination_data(app),
    )

    duplicate_data = valid_examination_data(app)
    duplicate_data["exam_code"] = "exam-cse301-2026"

    second_response = client.post(
        "/admin/examinations",
        data=duplicate_data,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        b"An examination with this examination code "
        b"already exists."
        in second_response.data
    )

    with app.app_context():
        examination_count = db.session.scalar(
            db.select(
                db.func.count(Examination.id)
            )
        )

        assert examination_count == 1


def test_admin_examinations_rejects_invalid_time_range():
    app = create_test_app()
    client = app.test_client()

    examination_data = valid_examination_data(app)
    examination_data["start_time"] = "13:00"
    examination_data["end_time"] = "10:00"

    response = client.post(
        "/admin/examinations",
        data=examination_data,
    )

    assert response.status_code == 200
    assert (
        b"End time must be later than start time."
        in response.data
    )

    with app.app_context():
        examination_count = db.session.scalar(
            db.select(
                db.func.count(Examination.id)
            )
        )

        assert examination_count == 0