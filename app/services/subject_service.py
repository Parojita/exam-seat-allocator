from app.extensions import db
from app.models import Branch, Subject


class SubjectValidationError(ValueError):
    pass


def parse_integer(value, error_message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise SubjectValidationError(
            error_message
        ) from None


def create_subject(form_data):
    subject_code = str(
        form_data.get("subject_code", "")
    ).strip().upper()

    if subject_code == "":
        raise SubjectValidationError(
            "Subject code is required."
        )

    name = str(
        form_data.get("name", "")
    ).strip()

    if name == "":
        raise SubjectValidationError(
            "Subject name is required."
        )

    branch_id = parse_integer(
        form_data.get("branch_id"),
        "Select a valid branch.",
    )

    branch = db.session.get(
        Branch,
        branch_id,
    )

    if branch is None:
        raise SubjectValidationError(
            "Select a valid branch."
        )

    semester = parse_integer(
        form_data.get("semester"),
        "Semester must be a whole number.",
    )

    if semester < 1 or semester > 8:
        raise SubjectValidationError(
            "Semester must be between 1 and 8."
        )

    exam_type = str(
        form_data.get("exam_type", "")
    ).strip()

    if exam_type == "":
        raise SubjectValidationError(
            "Exam type is required."
        )

    duration_minutes = parse_integer(
        form_data.get("duration_minutes"),
        "Duration must be a whole number.",
    )

    if (
        duration_minutes < 1
        or duration_minutes > 600
    ):
        raise SubjectValidationError(
            "Duration must be between "
            "1 and 600 minutes."
        )

    existing_subject = db.session.scalar(
        db.select(Subject).where(
            db.func.lower(
                Subject.subject_code
            ) == subject_code.casefold()
        )
    )

    if existing_subject is not None:
        raise SubjectValidationError(
            "A subject with this subject code "
            "already exists."
        )

    subject = Subject(
        subject_code=subject_code,
        name=name,
        branch=branch,
        semester=semester,
        exam_type=exam_type,
        duration_minutes=duration_minutes,
        active=True,
    )

    try:
        db.session.add(subject)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return subject