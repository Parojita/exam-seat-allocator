from io import BytesIO

from app import create_app


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


def test_admin_import_accepts_excel_filename():
    app = create_app({"TESTING": True})

    client = app.test_client()
    response = client.post(
        "/admin/import",
        data={
            "workbook": (
                BytesIO(b"temporary workbook content"),
                "students.xlsx",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"students.xlsx is ready for validation." in response.data