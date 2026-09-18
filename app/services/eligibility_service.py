from app.extensions import db
from app.models import (
    Student,
    StudentEligibility,
    Subject,
)


class EligibilityValidationError(ValueError):
    pass


def get_subject(subject_id):
    try:
        subject_id = int(subject_id)
    except (TypeError, ValueError):
        raise EligibilityValidationError(
            "Select a valid subject."
        ) from None

    subject = db.session.get(
        Subject,
        subject_id,
    )

    if subject is None:
        raise EligibilityValidationError(
            "Select a valid subject."
        )

    return subject


def get_matching_students(subject):
    return db.session.execute(
        db.select(Student)
        .where(
            Student.active.is_(True),
            Student.branch_id == subject.branch_id,
            Student.semester == subject.semester,
        )
        .order_by(Student.roll_number)
    ).scalars().all()


def parse_mark(
    value,
    minimum,
    maximum,
    field_label,
    roll_number,
):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise EligibilityValidationError(
            f"{field_label} for {roll_number} "
            "must be a number."
        ) from None

    if number < minimum or number > maximum:
        raise EligibilityValidationError(
            f"{field_label} for {roll_number} "
            f"must be between {minimum} and {maximum}."
        )

    return number


def calculate_eligibility(
    attendance_percentage,
    ppt_marks,
    assignment_marks,
    ct1_marks,
    ct2_marks,
    semester_fee_paid,
):
    reasons = []

    if attendance_percentage < 75:
        reasons.append(
            "Attendance must be at least 75%."
        )

    if ppt_marks < 4:
        reasons.append(
            "PPT marks must be at least 4/10."
        )

    if assignment_marks < 4:
        reasons.append(
            "Assignment marks must be at least 4/10."
        )

    ct_average = (
        ct1_marks + ct2_marks
    ) / 2

    if ct_average < 8:
        reasons.append(
            "CT average must be at least 8/20."
        )

    if not semester_fee_paid:
        reasons.append(
            "Semester fee must be paid."
        )

    return {
        "eligible": not reasons,
        "reasons": reasons,
        "ct_average": ct_average,
    }


def get_eligibility_view(subject_id):
    if subject_id in (None, ""):
        return {
            "subject": None,
            "rows": [],
            "matching_count": 0,
            "eligible_count": 0,
            "ineligible_count": 0,
        }

    subject = get_subject(subject_id)
    students = get_matching_students(subject)

    records = db.session.execute(
        db.select(StudentEligibility).where(
            StudentEligibility.subject_id
            == subject.id
        )
    ).scalars().all()

    records_by_student = {
        record.student_id: record
        for record in records
    }

    rows = []
    eligible_count = 0
    ineligible_count = 0

    for student in students:
        record = records_by_student.get(
            student.id
        )

        if record is None:
            rows.append(
                {
                    "student": student,
                    "record": None,
                    "result": None,
                }
            )
            continue

        result = calculate_eligibility(
            record.attendance_percentage,
            record.ppt_marks,
            record.assignment_marks,
            record.ct1_marks,
            record.ct2_marks,
            record.semester_fee_paid,
        )

        if result["eligible"]:
            eligible_count += 1
        else:
            ineligible_count += 1

        rows.append(
            {
                "student": student,
                "record": record,
                "result": result,
            }
        )

    return {
        "subject": subject,
        "rows": rows,
        "matching_count": len(students),
        "eligible_count": eligible_count,
        "ineligible_count": ineligible_count,
    }


def save_eligibility(subject_id, form_data):
    subject = get_subject(subject_id)
    students = get_matching_students(subject)

    validated_rows = []

    for student in students:
        student_id = student.id
        roll_number = student.roll_number

        attendance = parse_mark(
            form_data.get(
                f"attendance_{student_id}"
            ),
            0,
            100,
            "Attendance",
            roll_number,
        )

        ppt_marks = parse_mark(
            form_data.get(
                f"ppt_{student_id}"
            ),
            0,
            10,
            "PPT marks",
            roll_number,
        )

        assignment_marks = parse_mark(
            form_data.get(
                f"assignment_{student_id}"
            ),
            0,
            10,
            "Assignment marks",
            roll_number,
        )

        ct1_marks = parse_mark(
            form_data.get(
                f"ct1_{student_id}"
            ),
            0,
            20,
            "CT-1 marks",
            roll_number,
        )

        ct2_marks = parse_mark(
            form_data.get(
                f"ct2_{student_id}"
            ),
            0,
            20,
            "CT-2 marks",
            roll_number,
        )

        semester_fee_paid = (
            form_data.get(
                f"fee_paid_{student_id}"
            )
            == "yes"
        )

        result = calculate_eligibility(
            attendance,
            ppt_marks,
            assignment_marks,
            ct1_marks,
            ct2_marks,
            semester_fee_paid,
        )

        validated_rows.append(
            {
                "student": student,
                "attendance": attendance,
                "ppt_marks": ppt_marks,
                "assignment_marks": assignment_marks,
                "ct1_marks": ct1_marks,
                "ct2_marks": ct2_marks,
                "semester_fee_paid": (
                    semester_fee_paid
                ),
                "result": result,
            }
        )

    try:
        for row in validated_rows:
            student = row["student"]

            record = db.session.scalar(
                db.select(StudentEligibility)
                .where(
                    StudentEligibility.student_id
                    == student.id,
                    StudentEligibility.subject_id
                    == subject.id,
                )
            )

            if record is None:
                record = StudentEligibility(
                    student=student,
                    subject=subject,
                )

                db.session.add(record)

            record.attendance_percentage = (
                row["attendance"]
            )

            record.ppt_marks = row["ppt_marks"]

            record.assignment_marks = (
                row["assignment_marks"]
            )

            record.ct1_marks = row["ct1_marks"]
            record.ct2_marks = row["ct2_marks"]

            record.semester_fee_paid = (
                row["semester_fee_paid"]
            )

            record.eligible = row[
                "result"
            ]["eligible"]

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return get_eligibility_view(subject.id)