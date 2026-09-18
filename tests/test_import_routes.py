from io import BytesIO

from openpyxl import Workbook

from app import create_app


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


def test_admin_import_page_returns_success():
    app = create_app({"TESTING": True})

    client = app.test_client()
    response = client.get("/admin/import")

    assert response.status_code == 200
    assert b"Import Examination Data" in response.data


def test_admin_import_rejects_non_excel_file():
    app = create_app({"TESTING": True})

    client = app.test_client()
    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                BytesIO(b"not an Excel workbook"),
                "students.txt",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Only .xlsx files are accepted." in response.data


def test_admin_import_validates_student_workbook():
    app = create_app({"TESTING": True})

    workbook_file = create_workbook(
        [
            "roll_number",
            "name",
            "branch_code",
            "semester",
            "email",
            "photo_path",
            "special_request",
            "rfid_uid",
        ],
        [
            [
                "CSE001",
                "Aarav Sharma",
                "CSE",
                6,
                "aarav@example.edu",
                None,
                None,
                None,
            ],
            [
                "ECE001",
                "Diya Sen",
                "ECE",
                6,
                "diya@example.edu",
                None,
                None,
                None,
            ],
        ],
    )

    client = app.test_client()
    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                workbook_file,
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

   

    assert b"2 student rows found." in response.data
    assert b"Workbook is ready for import preview." in response.data


def test_admin_import_displays_missing_columns():
    app = create_app({"TESTING": True})

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

    client = app.test_client()
    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                workbook_file,
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Workbook validation failed." in response.data
    assert b"email" in response.data
    assert b"photo_path" in response.data
    assert b"special_request" in response.data
    assert b"rfid_uid" in response.data
def test_admin_import_displays_student_row_errors():
    workbook_file = create_workbook(
        [
            "roll_number",
            "name",
            "branch_code",
            "semester",
            "email",
            "photo_path",
            "special_request",
            "rfid_uid",
        ],
        [
            [
                "CSE001",
                None,
                "CSE",
                6,
                "aarav@example.edu",
                None,
                None,
                None,
            ],
        ],
    )

    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                workbook_file,
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Workbook validation failed." in response.data
    assert b"Row 2" in response.data
    assert b"name is required." in response.data
def test_admin_import_rejects_missing_file():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post(
        "/admin/import",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Select an Excel workbook." in response.data


def test_admin_import_rejects_corrupted_excel_file():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                BytesIO(b"not a real Excel workbook"),
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert (
        b"The uploaded file is not a valid Excel workbook."
        in response.data
    )


def test_admin_import_displays_invalid_semester_error():
    workbook_file = create_workbook(
        [
            "roll_number",
            "name",
            "branch_code",
            "semester",
            "email",
            "photo_path",
            "special_request",
            "rfid_uid",
        ],
        [
            [
                "CSE001",
                "Aarav Sharma",
                "CSE",
                9,
                "aarav@example.edu",
                None,
                None,
                None,
            ],
        ],
    )

    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                workbook_file,
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Row 2" in response.data
    assert (
        b"semester must be between 1 and 8."
        in response.data
    )


def test_admin_import_displays_duplicate_roll_number_error():
    workbook_file = create_workbook(
        [
            "roll_number",
            "name",
            "branch_code",
            "semester",
            "email",
            "photo_path",
            "special_request",
            "rfid_uid",
        ],
        [
            [
                "CSE001",
                "Aarav Sharma",
                "CSE",
                6,
                "aarav@example.edu",
                None,
                None,
                None,
            ],
            [
                "CSE001",
                "Diya Sen",
                "ECE",
                6,
                "diya@example.edu",
                None,
                None,
                None,
            ],
        ],
    )

    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                workbook_file,
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Row 3" in response.data
    assert (
        b"roll_number is duplicated in the workbook."
        in response.data
    )