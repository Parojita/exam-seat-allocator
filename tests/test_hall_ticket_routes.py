from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import (
    AllocationRun,
    Branch,
    Examination,
    Room,
    Seat,
    SeatAllocation,
    Student,
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


def create_allocated_student(app):
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
            email="student@example.com",
            active=True,
        )

        room = Room(
            room_number="R101",
            building="Main Building",
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

        allocation_run = AllocationRun(
            examination=examination,
            seed=1,
            status="completed",
        )

        allocation = SeatAllocation(
            allocation_run=allocation_run,
            examination=examination,
            student=student,
            seat=seat,
        )

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                student,
                room,
                seat,
                allocation_run,
                allocation,
            ]
        )

        db.session.commit()

        return allocation.id


def test_hall_ticket_route_returns_pdf():
    app = create_test_app()
    allocation_id = create_allocated_student(app)
    client = app.test_client()

    response = client.get(
        f"/hall-ticket/{allocation_id}.pdf"
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")

    content_disposition = response.headers.get(
        "Content-Disposition",
        "",
    )

    assert "CSE001_hall_ticket.pdf" in (
        content_disposition
    )