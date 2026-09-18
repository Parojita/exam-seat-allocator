from datetime import date, time

from app.extensions import db
from app.models import Examination, Subject


class ExaminationValidationError(ValueError):
    pass


def parse_integer(value, error_message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ExaminationValidationError(
            error_message
        ) from None


def parse_date(value):
    try:
        return date.fromisoformat(
            str(value).strip()
        )
    except (TypeError, ValueError):
        raise ExaminationValidationError(
            "Enter a valid examination date."
        ) from None


def parse_time(value, error_message):
    try:
        return time.fromisoformat(
            str(value).strip()
        )
    except (TypeError, ValueError):
        raise ExaminationValidationError(
            error_message
        ) from None


def create_examination(form_data):
    exam_code = str(
        form_data.get("exam_code", "")
    ).strip().upper()

    if exam_code == "":
        raise ExaminationValidationError(
            "Examination code is required."
        )

    subject_id = parse_integer(
        form_data.get("subject_id"),
        "Select a valid subject.",
    )

    subject = db.session.get(
        Subject,
        subject_id,
    )

    if subject is None:
        raise ExaminationValidationError(
            "Select a valid subject."
        )

    exam_date = parse_date(
        form_data.get("exam_date")
    )

    start_time = parse_time(
        form_data.get("start_time"),
        "Enter a valid start time.",
    )

    end_time = parse_time(
        form_data.get("end_time"),
        "Enter a valid end time.",
    )

    if end_time <= start_time:
        raise ExaminationValidationError(
            "End time must be later than start time."
        )

    exam_type = str(
        form_data.get("exam_type", "")
    ).strip()

    if exam_type == "":
        raise ExaminationValidationError(
            "Exam type is required."
        )

    existing_examination = db.session.scalar(
        db.select(Examination).where(
            db.func.lower(
                Examination.exam_code
            ) == exam_code.casefold()
        )
    )

    if existing_examination is not None:
        raise ExaminationValidationError(
            "An examination with this examination "
            "code already exists."
        )

    examination = Examination(
        exam_code=exam_code,
        subject=subject,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        exam_type=exam_type,
    )

    try:
        db.session.add(examination)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return examination