from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Examination,
    Room,
    Seat,
    SeatAllocation,
    Student,
    StudentEligibility,
    Subject,
)


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": (
                "sqlite:///:memory:"
            ),
        }
    )

    with app.app_context():
        db.create_all()

    return app


def create_allocation_data(app):
    with app.app_context():
        branch = Branch(
            code="CSE",
            name="Computer Science",
        )

        subject = Subject(
            subject_code="CSE401",
            name="Artificial Intelligence",
            branch=branch,
            semester=6,
            exam_type="End Semester",
            duration_minutes=180,
            active=True,
        )

        examination = Examination(
            exam_code="EXAM-CSE401",
            subject=subject,
            exam_date=date(2026, 10, 10),
            start_time=time(10, 0),
            end_time=time(13, 0),
            exam_type="End Semester",
        )

        student = Student(
            roll_number="CSE001",
            name="Test Student",
            branch=branch,
            semester=6,
            active=True,
        )

        eligibility = StudentEligibility(
            student=student,
            subject=subject,
            attendance_percentage=80,
            ppt_marks=8,
            assignment_marks=8,
            ct1_marks=12,
            ct2_marks=12,
            semester_fee_paid=True,
            eligible=True,
        )

        room = Room(
            room_number="R101",
            building="Main",
            floor=0,
            rows=1,
            columns=1,
            students_per_desk=1,
            exam_capacity=1,
        )

        seat = Seat(
            room=room,
            desk_code="D1",
            seat_code="S1",
            row_code="A",
            column_code="1",
            accessible=False,
            active=True,
        )

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                student,
                eligibility,
                room,
                seat,
            ]
        )

        db.session.commit()

        return examination.id


def test_admin_allocations_page_returns_success():
    app = create_test_app()
    client = app.test_client()

    response = client.get(
        "/admin/allocations"
    )

    assert response.status_code == 200
    assert b"Seating Allocation" in response.data
    assert b"Select Examination" in response.data


def test_allocation_page_lists_examination():
    app = create_test_app()
    examination_id = create_allocation_data(app)
    client = app.test_client()

    response = client.get(
        "/admin/allocations"
        f"?examination_id={examination_id}"
    )

    assert response.status_code == 200
    assert b"EXAM-CSE401" in response.data
    assert b"Generate Seating Plan" in response.data


def test_admin_can_generate_allocation():
    app = create_test_app()
    examination_id = create_allocation_data(app)
    client = app.test_client()

    response = client.post(
        "/admin/allocations",
        data={
            "examination_id": examination_id,
            "action": "allocate",
        },
    )

    assert response.status_code == 200

    assert (
        b"Seating allocation completed"
        in response.data
    )

    assert b"CSE001" in response.data
    assert b"R101" in response.data
    assert b"S1" in response.data

    with app.app_context():
        allocation_count = db.session.scalar(
            db.select(
                db.func.count(SeatAllocation.id)
            )
        )

        assert allocation_count == 1


def test_navigation_contains_allocation_link():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"/admin/allocations" in response.data
    assert b"Allocations" in response.data