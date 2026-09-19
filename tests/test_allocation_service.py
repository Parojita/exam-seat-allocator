from datetime import date, time

import pytest

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
    StudentEligibility,
    Subject,
)
from app.services.allocation_service import (
    AllocationError,
    allocate_examination,
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


def create_branch(code):
    return Branch(
        code=code,
        name=f"{code} Department",
    )


def create_subject(code, branch):
    return Subject(
        subject_code=code,
        name=f"{code} Subject",
        branch=branch,
        semester=6,
        exam_type="End Semester",
        duration_minutes=180,
        active=True,
    )


def create_examination(code, subject):
    return Examination(
        exam_code=code,
        subject=subject,
        exam_date=date(2026, 10, 1),
        start_time=time(10, 0),
        end_time=time(13, 0),
        exam_type="End Semester",
    )


def create_student(
    roll_number,
    branch,
    special_request=None,
):
    return Student(
        roll_number=roll_number,
        name=f"Student {roll_number}",
        branch=branch,
        semester=6,
        special_request=special_request,
        active=True,
    )


def create_eligibility(
    student,
    subject,
    eligible=True,
):
    return StudentEligibility(
        student=student,
        subject=subject,
        attendance_percentage=80,
        ppt_marks=8,
        assignment_marks=8,
        ct1_marks=12,
        ct2_marks=12,
        semester_fee_paid=True,
        eligible=eligible,
    )


def create_room_with_seats(
    seat_count,
    accessible_positions=None,
):
    accessible_positions = (
        accessible_positions or set()
    )

    room = Room(
        room_number="R101",
        building="Main",
        floor=0,
        rows=1,
        columns=seat_count,
        students_per_desk=1,
        exam_capacity=seat_count,
    )

    seats = []

    for position in range(1, seat_count + 1):
        seats.append(
            Seat(
                room=room,
                desk_code=f"D{position}",
                seat_code=f"S{position}",
                row_code="A",
                column_code=str(position),
                accessible=(
                    position
                    in accessible_positions
                ),
                active=True,
            )
        )

    return room, seats


def test_allocator_assigns_only_eligible_students():
    app = create_test_app()

    with app.app_context():
        branch = create_branch("CSE")
        subject = create_subject("CSE301", branch)

        examination = create_examination(
            "EXAM-CSE301",
            subject,
        )

        eligible_student = create_student(
            "CSE001",
            branch,
        )

        ineligible_student = create_student(
            "CSE002",
            branch,
        )

        room, seats = create_room_with_seats(2)

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                eligible_student,
                ineligible_student,
                create_eligibility(
                    eligible_student,
                    subject,
                    eligible=True,
                ),
                create_eligibility(
                    ineligible_student,
                    subject,
                    eligible=False,
                ),
                room,
                *seats,
            ]
        )

        db.session.commit()

        allocate_examination(examination.id)

        allocations = db.session.execute(
            db.select(SeatAllocation)
        ).scalars().all()

        assert len(allocations) == 1

        assert (
            allocations[0].student.roll_number
            == "CSE001"
        )


def test_allocator_never_duplicates_a_seat():
    app = create_test_app()

    with app.app_context():
        branch = create_branch("CSE")
        subject = create_subject("CSE302", branch)

        examination = create_examination(
            "EXAM-CSE302",
            subject,
        )

        students = [
            create_student("CSE001", branch),
            create_student("CSE002", branch),
        ]

        room, seats = create_room_with_seats(2)

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                *students,
                *[
                    create_eligibility(
                        student,
                        subject,
                    )
                    for student in students
                ],
                room,
                *seats,
            ]
        )

        db.session.commit()

        allocate_examination(examination.id)

        allocations = db.session.execute(
            db.select(SeatAllocation)
        ).scalars().all()

        student_ids = {
            allocation.student_id
            for allocation in allocations
        }

        seat_ids = {
            allocation.seat_id
            for allocation in allocations
        }

        assert len(allocations) == 2
        assert len(student_ids) == 2
        assert len(seat_ids) == 2


def test_insufficient_capacity_saves_nothing():
    app = create_test_app()

    with app.app_context():
        branch = create_branch("CSE")
        subject = create_subject("CSE303", branch)

        examination = create_examination(
            "EXAM-CSE303",
            subject,
        )

        students = [
            create_student("CSE001", branch),
            create_student("CSE002", branch),
        ]

        room, seats = create_room_with_seats(1)

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                *students,
                *[
                    create_eligibility(
                        student,
                        subject,
                    )
                    for student in students
                ],
                room,
                *seats,
            ]
        )

        db.session.commit()

        with pytest.raises(
            AllocationError,
            match="Insufficient seating capacity",
        ):
            allocate_examination(examination.id)

        allocation_count = db.session.scalar(
            db.select(
                db.func.count(SeatAllocation.id)
            )
        )

        run_count = db.session.scalar(
            db.select(
                db.func.count(AllocationRun.id)
            )
        )

        assert allocation_count == 0
        assert run_count == 0


def test_accessibility_student_gets_accessible_seat():
    app = create_test_app()

    with app.app_context():
        branch = create_branch("CSE")
        subject = create_subject("CSE304", branch)

        examination = create_examination(
            "EXAM-CSE304",
            subject,
        )

        student = create_student(
            "CSE001",
            branch,
            special_request="Wheelchair access",
        )

        room, seats = create_room_with_seats(
            2,
            accessible_positions={2},
        )

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                student,
                create_eligibility(
                    student,
                    subject,
                ),
                room,
                *seats,
            ]
        )

        db.session.commit()

        allocate_examination(examination.id)

        allocation = db.session.scalar(
            db.select(SeatAllocation)
        )

        assert allocation is not None
        assert allocation.seat.accessible is True


def test_repeated_allocation_preserves_saved_plan():
    app = create_test_app()

    with app.app_context():
        branch = create_branch("CSE")
        subject = create_subject("CSE305", branch)

        examination = create_examination(
            "EXAM-CSE305",
            subject,
        )

        student = create_student(
            "CSE001",
            branch,
        )

        room, seats = create_room_with_seats(2)

        db.session.add_all(
            [
                branch,
                subject,
                examination,
                student,
                create_eligibility(
                    student,
                    subject,
                ),
                room,
                *seats,
            ]
        )

        db.session.commit()

        first_run = allocate_examination(
            examination.id
        )

        first_run_id = first_run.id
        first_seed = first_run.seed

        first_seat_id = db.session.scalar(
            db.select(SeatAllocation.seat_id)
        )

        second_run = allocate_examination(
            examination.id
        )

        second_seat_id = db.session.scalar(
            db.select(SeatAllocation.seat_id)
        )

        assert second_run.id == first_run_id
        assert second_run.seed == first_seed
        assert second_seat_id == first_seat_id


def test_simultaneous_examinations_cannot_reuse_seat():
    app = create_test_app()

    with app.app_context():
        cse = create_branch("CSE")
        ece = create_branch("ECE")

        cse_subject = create_subject(
            "CSE306",
            cse,
        )

        ece_subject = create_subject(
            "ECE306",
            ece,
        )

        cse_exam = create_examination(
            "EXAM-CSE306",
            cse_subject,
        )

        ece_exam = create_examination(
            "EXAM-ECE306",
            ece_subject,
        )

        cse_student = create_student(
            "CSE001",
            cse,
        )

        ece_student = create_student(
            "ECE001",
            ece,
        )

        room, seats = create_room_with_seats(1)

        db.session.add_all(
            [
                cse,
                ece,
                cse_subject,
                ece_subject,
                cse_exam,
                ece_exam,
                cse_student,
                ece_student,
                create_eligibility(
                    cse_student,
                    cse_subject,
                ),
                create_eligibility(
                    ece_student,
                    ece_subject,
                ),
                room,
                *seats,
            ]
        )

        db.session.commit()

        allocate_examination(cse_exam.id)

        with pytest.raises(
            AllocationError,
            match="Insufficient seating capacity",
        ):
            allocate_examination(ece_exam.id)