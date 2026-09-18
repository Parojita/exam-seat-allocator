from app import create_app
from app.extensions import db
from app.models import Branch, Subject


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

        db.session.add(branch)
        db.session.commit()

    return app


def get_branch_id(app):
    with app.app_context():
        branch = db.session.scalar(
            db.select(Branch).where(
                Branch.code == "CSE"
            )
        )

        return branch.id


def valid_subject_data(app):
    return {
        "subject_code": "CSE301",
        "name": "Database Systems",
        "branch_id": str(get_branch_id(app)),
        "semester": "6",
        "exam_type": "End Semester",
        "duration_minutes": "180",
    }


def test_admin_subjects_page_returns_success():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/admin/subjects")

    assert response.status_code == 200
    assert b"Subject Management" in response.data
    assert b"Add Subject" in response.data
    assert b"CSE" in response.data


def test_admin_subjects_creates_subject():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/subjects",
        data=valid_subject_data(app),
    )

    assert response.status_code == 200
    assert (
        b"Subject CSE301 created successfully."
        in response.data
    )

    with app.app_context():
        subject = db.session.scalar(
            db.select(Subject).where(
                Subject.subject_code == "CSE301"
            )
        )

        assert subject is not None
        assert subject.name == "Database Systems"
        assert subject.branch.code == "CSE"
        assert subject.semester == 6
        assert subject.exam_type == "End Semester"
        assert subject.duration_minutes == 180
        assert subject.active is True


def test_admin_subjects_rejects_duplicate_code():
    app = create_test_app()
    client = app.test_client()

    first_response = client.post(
        "/admin/subjects",
        data=valid_subject_data(app),
    )

    duplicate_data = valid_subject_data(app)
    duplicate_data["subject_code"] = "cse301"
    duplicate_data["name"] = "Duplicate Subject"

    second_response = client.post(
        "/admin/subjects",
        data=duplicate_data,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        b"A subject with this subject code already exists."
        in second_response.data
    )

    with app.app_context():
        subject_count = db.session.scalar(
            db.select(
                db.func.count(Subject.id)
            )
        )

        assert subject_count == 1


def test_admin_subjects_rejects_invalid_semester():
    app = create_test_app()
    client = app.test_client()

    subject_data = valid_subject_data(app)
    subject_data["semester"] = "9"

    response = client.post(
        "/admin/subjects",
        data=subject_data,
    )

    assert response.status_code == 200
    assert (
        b"Semester must be between 1 and 8."
        in response.data
    )

    with app.app_context():
        subject_count = db.session.scalar(
            db.select(
                db.func.count(Subject.id)
            )
        )

        assert subject_count == 0