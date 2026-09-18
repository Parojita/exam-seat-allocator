from io import BytesIO

from openpyxl import Workbook

from app.services.workbook_validator import (
    STUDENT_REQUIRED_COLUMNS,
    validate_student_workbook,
)


def create_workbook(columns, rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(columns)

    for row in rows:
        worksheet.append(row)

    workbook_file = BytesIO()
    workbook.save(workbook_file)
    workbook_file.seek(0)

    return workbook_file


def create_student_row(
    roll_number="CSE001",
    name="Aarav Sharma",
    branch_code="CSE",
    semester=6,
    email="aarav@example.edu",
    photo_path=None,
    special_request=None,
    rfid_uid=None,
):
    return [
        roll_number,
        name,
        branch_code,
        semester,
        email,
        photo_path,
        special_request,
        rfid_uid,
    ]


def test_valid_student_workbook_returns_row_count():
    workbook_file = create_workbook(
        STUDENT_REQUIRED_COLUMNS,
        [
            create_student_row(),
            create_student_row(
                roll_number="ECE001",
                name="Diya Sen",
                branch_code="ECE",
                email="diya@example.edu",
            ),
        ],
    )

    result = validate_student_workbook(workbook_file)

    assert result["valid"] is True
    assert result["row_count"] == 2
    assert result["missing_columns"] == []


def test_student_workbook_reports_missing_columns():
    workbook_file = create_workbook(
        [
            "roll_number",
            "name",
            "branch_code",
            "semester",
        ],
        [
            [
                "CSE001",
                "Aarav Sharma",
                "CSE",
                6,
            ],
        ],
    )

    result = validate_student_workbook(workbook_file)

    assert result["valid"] is False
    assert result["missing_columns"] == [
        "email",
        "photo_path",
        "special_request",
        "rfid_uid",
    ]


def test_student_workbook_rejects_missing_required_value():
    workbook_file = create_workbook(
        STUDENT_REQUIRED_COLUMNS,
        [
            create_student_row(name=None),
        ],
    )

    result = validate_student_workbook(workbook_file)

    assert result["valid"] is False
    assert result["row_errors"] == [
        {
            "row_number": 2,
            "messages": [
                "name is required.",
            ],
        }
    ]


def test_student_workbook_rejects_invalid_semester():
    workbook_file = create_workbook(
        STUDENT_REQUIRED_COLUMNS,
        [
            create_student_row(semester=9),
        ],
    )

    result = validate_student_workbook(workbook_file)

    assert result["valid"] is False
    assert result["row_errors"] == [
        {
            "row_number": 2,
            "messages": [
                "semester must be between 1 and 8.",
            ],
        }
    ]


def test_student_workbook_rejects_duplicate_roll_number():
    workbook_file = create_workbook(
        STUDENT_REQUIRED_COLUMNS,
        [
            create_student_row(),
            create_student_row(
                roll_number="CSE001",
                name="Riya Saha",
                email="riya@example.edu",
            ),
        ],
    )

    result = validate_student_workbook(workbook_file)

    assert result["valid"] is False
    assert result["row_errors"] == [
        {
            "row_number": 3,
            "messages": [
                "roll_number is duplicated in the workbook.",
            ],
        }
    ]