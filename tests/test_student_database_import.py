from io import BytesIO

from openpyxl import Workbook

from app import create_app
from app.extensions import db
from app.models import Branch, Student


STUDENT_COLUMNS = [
    "roll_number",
    "name",
    "branch_code",
    "semester",
    "email",
    "photo_path",
    "special_request",
    "rfid_uid",
]


def create_student_workbook():
    workbook = Workbook()
    worksheet = workbook.active

    worksheet.append(STUDENT_COLUMNS)

    worksheet.append(
        [
            "CSE001",
            "Aarav Sharma",
            "CSE",
            6,
            "aarav@example.edu",
            "photos/CSE001.jpg",
            None,
            None,
        ]
    )

    worksheet.append(
        [
            "ECE001",
            "Diya Sen",
            "ECE",
            6,
            "diya@example.edu",
            "photos/ECE001.jpg",
            "Front row",
            "RFID-ECE001",
        ]
    )

    workbook_file = BytesIO()
    workbook.save(workbook_file)
    workbook_file.seek(0)

    return workbook_file


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()

    return app


def upload_student_workbook(client):
        return client.post(
        "/admin/import",
        data={
            "action": "import",
            "workbook": (
                create_student_workbook(),
                "students.xlsx",
            ),
        },
        content_type="multipart/form-data",
    )


def test_valid_workbook_imports_students_and_branches():
    app = create_test_app()
    client = app.test_client()

    response = upload_student_workbook(client)

    assert response.status_code == 200

    with app.app_context():
        assert db.session.scalar(
            db.select(db.func.count(Student.id))
        ) == 2

        assert db.session.scalar(
            db.select(db.func.count(Branch.id))
        ) == 2

        student = db.session.scalar(
            db.select(Student).where(
                Student.roll_number == "ECE001"
            )
        )

        assert student is not None
        assert student.name == "Diya Sen"
        assert student.branch.code == "ECE"
        assert student.semester == 6
        assert student.email == "diya@example.edu"
        assert student.photo_path == "photos/ECE001.jpg"
        assert student.special_request == "Front row"
        assert student.rfid_uid == "RFID-ECE001"

    assert b"2 students imported." in response.data
    assert b"0 existing students skipped." in response.data


def test_uploading_same_workbook_skips_existing_students():
    app = create_test_app()
    client = app.test_client()

    first_response = upload_student_workbook(client)
    second_response = upload_student_workbook(client)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    with app.app_context():
        assert db.session.scalar(
            db.select(db.func.count(Student.id))
        ) == 2

        assert db.session.scalar(
            db.select(db.func.count(Branch.id))
        ) == 2

    assert b"0 students imported." in second_response.data
    assert b"2 existing students skipped." in second_response.data