from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Student,
    StudentEligibility,
    Subject,
)


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()

        cse = Branch(
            code="CSE",
            name="Computer Science and Engineering",
        )

        ece = Branch(
            code="ECE",
            name="Electronics and Communication",
        )

        subject = Subject(
            subject_code="CSE301",
            name="Database Systems",
            branch=cse,
            semester=6,
            exam_type="End Semester",
            duration_minutes=180,
            active=True,
        )

        students = [
            Student(
                roll_number="CSE001",
                name="Aarav Sharma",
                branch=cse,
                semester=6,
                active=True,
            ),
            Student(
                roll_number="CSE002",
                name="Diya Sen",
                branch=cse,
                semester=6,
                active=True,
            ),
            Student(
                roll_number="CSE003",
                name="Wrong Semester",
                branch=cse,
                semester=5,
                active=True,
            ),
            Student(
                roll_number="CSE004",
                name="Inactive Student",
                branch=cse,
                semester=6,
                active=False,
            ),
            Student(
                roll_number="ECE001",
                name="Wrong Branch",
                branch=ece,
                semester=6,
                active=True,
            ),
        ]

        db.session.add_all(
            [
                cse,
                ece,
                subject,
                *students,
            ]
        )

        db.session.commit()

    return app


def get_record_ids(app):
    with app.app_context():
        subject = db.session.scalar(
            db.select(Subject).where(
                Subject.subject_code == "CSE301"
            )
        )

        students = {
            student.roll_number: student.id
            for student in db.session.execute(
                db.select(Student)
            ).scalars()
        }

        return subject.id, students


def valid_eligibility_data(app):
    subject_id, student_ids = get_record_ids(app)

    cse001 = student_ids["CSE001"]
    cse002 = student_ids["CSE002"]

    return {
        "subject_id": str(subject_id),

        f"attendance_{cse001}": "82",
        f"ppt_{cse001}": "7",
        f"assignment_{cse001}": "6",
        f"ct1_{cse001}": "10",
        f"ct2_{cse001}": "12",
        f"fee_paid_{cse001}": "yes",

        f"attendance_{cse002}": "70",
        f"ppt_{cse002}": "3",
        f"assignment_{cse002}": "6",
        f"ct1_{cse002}": "6",
        f"ct2_{cse002}": "8",
    }


def test_admin_eligibility_page_returns_success():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/admin/eligibility")

    assert response.status_code == 200
    assert b"Student Eligibility" in response.data
    assert b"Select Subject" in response.data
    assert b"CSE301" in response.data


def test_admin_eligibility_matches_correct_students():
    app = create_test_app()
    client = app.test_client()
    subject_id, _ = get_record_ids(app)

    response = client.get(
        f"/admin/eligibility?subject_id={subject_id}"
    )

    assert response.status_code == 200
    assert b"CSE001" in response.data
    assert b"CSE002" in response.data

    assert b"CSE003" not in response.data
    assert b"CSE004" not in response.data
    assert b"ECE001" not in response.data

    assert b"2 matching students" in response.data


def test_admin_eligibility_calculates_and_saves_results():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/admin/eligibility",
        data=valid_eligibility_data(app),
    )

    assert response.status_code == 200

    assert (
        b"Eligibility saved: 1 eligible, 1 ineligible."
        in response.data
    )

    assert b"Attendance must be at least 75%." in response.data
    assert b"PPT marks must be at least 4/10." in response.data
    assert b"CT average must be at least 8/20." in response.data
    assert b"Semester fee must be paid." in response.data

    with app.app_context():
        records = db.session.execute(
            db.select(StudentEligibility)
            .join(Student)
            .order_by(Student.roll_number)
        ).scalars().all()

        assert len(records) == 2

        by_roll_number = {
            record.student.roll_number: record
            for record in records
        }

        eligible_record = by_roll_number["CSE001"]

        assert eligible_record.attendance_percentage == 82
        assert eligible_record.ppt_marks == 7
        assert eligible_record.assignment_marks == 6
        assert eligible_record.ct1_marks == 10
        assert eligible_record.ct2_marks == 12
        assert eligible_record.semester_fee_paid is True
        assert eligible_record.eligible is True

        ineligible_record = by_roll_number["CSE002"]

        assert ineligible_record.attendance_percentage == 70
        assert ineligible_record.ppt_marks == 3
        assert ineligible_record.assignment_marks == 6
        assert ineligible_record.ct1_marks == 6
        assert ineligible_record.ct2_marks == 8
        assert ineligible_record.semester_fee_paid is False
        assert ineligible_record.eligible is False


def test_admin_eligibility_rejects_marks_outside_range():
    app = create_test_app()
    client = app.test_client()
    _, student_ids = get_record_ids(app)

    form_data = valid_eligibility_data(app)
    cse001 = student_ids["CSE001"]
    form_data[f"ppt_{cse001}"] = "11"

    response = client.post(
        "/admin/eligibility",
        data=form_data,
    )

    assert response.status_code == 200

    assert (
        b"PPT marks for CSE001 must be between 0 and 10."
        in response.data
    )

    with app.app_context():
        record_count = db.session.scalar(
            db.select(
                db.func.count(StudentEligibility.id)
            )
        )

        assert record_count == 0


def test_admin_eligibility_ignores_nonmatching_students():
    app = create_test_app()
    client = app.test_client()
    _, student_ids = get_record_ids(app)

    form_data = valid_eligibility_data(app)

    ece001 = student_ids["ECE001"]

    form_data.update(
        {
            f"attendance_{ece001}": "100",
            f"ppt_{ece001}": "10",
            f"assignment_{ece001}": "10",
            f"ct1_{ece001}": "20",
            f"ct2_{ece001}": "20",
            f"fee_paid_{ece001}": "yes",
        }
    )

    response = client.post(
        "/admin/eligibility",
        data=form_data,
    )

    assert response.status_code == 200

    with app.app_context():
        records = db.session.execute(
            db.select(StudentEligibility)
        ).scalars().all()

        recorded_students = {
            record.student.roll_number
            for record in records
        }

        assert recorded_students == {
            "CSE001",
            "CSE002",
        }

        assert "ECE001" not in recorded_students