from pathlib import Path
from zipfile import BadZipFile

from flask import Blueprint, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    Branch,
    Examination,
    Room,
    Subject,
)
from app.services.examination_service import (
    ExaminationValidationError,
    create_examination,
)
from app.services.room_service import (
    RoomValidationError,
    create_room_with_seats,
)
from app.services.student_importer import (
    import_student_workbook,
)
from app.services.subject_service import (
    SubjectValidationError,
    create_subject,
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
            extension = Path(
                workbook.filename
            ).suffix.lower()

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

                except (
                    BadZipFile,
                    OSError,
                    ValueError,
                ):
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


@main.route("/admin/rooms", methods=["GET", "POST"])
def admin_rooms():
    error_message = None
    success_message = None

    if request.method == "POST":
        try:
            room = create_room_with_seats(
                request.form
            )

            success_message = (
                f"Room {room.room_number} created "
                f"with {room.capacity} seats."
            )

        except RoomValidationError as error:
            error_message = str(error)

        except SQLAlchemyError:
            error_message = (
                "The room could not be created. "
                "No database changes were saved."
            )

    rooms = db.session.execute(
        db.select(Room).order_by(
            Room.room_number
        )
    ).scalars().all()

    return render_template(
        "admin_rooms.html",
        rooms=rooms,
        error_message=error_message,
        success_message=success_message,
    )


@main.route("/admin/subjects", methods=["GET", "POST"])
def admin_subjects():
    error_message = None
    success_message = None

    if request.method == "POST":
        try:
            subject = create_subject(
                request.form
            )

            success_message = (
                f"Subject {subject.subject_code} "
                "created successfully."
            )

        except SubjectValidationError as error:
            error_message = str(error)

        except SQLAlchemyError:
            error_message = (
                "The subject could not be created. "
                "No database changes were saved."
            )

    branches = db.session.execute(
        db.select(Branch).order_by(
            Branch.code
        )
    ).scalars().all()

    subjects = db.session.execute(
        db.select(Subject).order_by(
            Subject.subject_code
        )
    ).scalars().all()

    return render_template(
        "admin_subjects.html",
        branches=branches,
        subjects=subjects,
        error_message=error_message,
        success_message=success_message,
    )
@main.route(
    "/admin/examinations",
    methods=["GET", "POST"],
)
def admin_examinations():
    error_message = None
    success_message = None

    if request.method == "POST":
        try:
            examination = create_examination(
                request.form
            )

            success_message = (
                f"Examination {examination.exam_code} "
                "created successfully."
            )

        except ExaminationValidationError as error:
            error_message = str(error)

        except SQLAlchemyError:
            error_message = (
                "The examination could not be created. "
                "No database changes were saved."
            )

    subjects = db.session.execute(
        db.select(Subject)
        .where(Subject.active.is_(True))
        .order_by(Subject.subject_code)
    ).scalars().all()

    examinations = db.session.execute(
        db.select(Examination).order_by(
            Examination.exam_date,
            Examination.start_time,
        )
    ).scalars().all()

    return render_template(
        "admin_examinations.html",
        subjects=subjects,
        examinations=examinations,
        error_message=error_message,
        success_message=success_message,
    )