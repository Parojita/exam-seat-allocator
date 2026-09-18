from pathlib import Path

from flask import Blueprint, render_template, request


main = Blueprint("main", __name__)


@main.get("/")
def home():
    return render_template("index.html")


@main.route("/admin/import", methods=["GET", "POST"])
def admin_import():
    error_message = None
    success_message = None

    if request.method == "POST":
        workbook = request.files.get("workbook")

        if workbook is None or workbook.filename == "":
            error_message = "Select an Excel workbook."
        else:
            extension = Path(workbook.filename).suffix.lower()

            if extension != ".xlsx":
                error_message = "Only .xlsx files are accepted."
            else:
                success_message = (
                    f"{workbook.filename} is ready for validation."
                )

    return render_template(
        "admin_import.html",
        error_message=error_message,
        success_message=success_message,
    )