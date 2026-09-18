from pathlib import Path
from zipfile import BadZipFile

from flask import Blueprint, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from app.services.student_importer import (
    import_student_workbook,
)
from app.services.workbook_validator import (
    validate_student_workbook,
)


main = Blueprint("main", __name__)


@main.get("/")
def home():
    return render_template("index.html")


@main.route("/admin/import", methods=["GET", "POST"])
def admin_import():
    error_message = None
    validation_result = None
    import_result = None
    uploaded_filename = None

    if request.method == "POST":
        workbook = request.files.get("workbook")

        if workbook is None or workbook.filename == "":
            error_message = "Select an Excel workbook."
        else:
            uploaded_filename = workbook.filename
            extension = Path(workbook.filename).suffix.lower()

            if extension != ".xlsx":
                error_message = (
                    "Only .xlsx files are accepted."
                )
            else:
                try:
                    validation_result = (
                        validate_student_workbook(
                            workbook.stream
                        )
                    )

                    should_import = (
                        request.form.get("action")
                        == "import"
                    )

                    if (
                        validation_result["valid"]
                        and should_import
                    ):
                        workbook.stream.seek(0)

                        import_result = (
                            import_student_workbook(
                                workbook.stream
                            )
                        )

                except (BadZipFile, OSError, ValueError):
                    error_message = (
                        "The uploaded file is not a valid "
                        "Excel workbook."
                    )

                except SQLAlchemyError:
                    error_message = (
                        "The students could not be imported. "
                        "No database changes were saved."
                    )

    return render_template(
        "admin_import.html",
        error_message=error_message,
        validation_result=validation_result,
        import_result=import_result,
        uploaded_filename=uploaded_filename,
    )