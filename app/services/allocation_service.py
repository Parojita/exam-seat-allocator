import random

import pulp

from app.extensions import db
from app.models import (
    AllocationRun,
    Examination,
    Seat,
    SeatAdjacency,
    SeatAllocation,
    Student,
    StudentEligibility,
)


class AllocationError(ValueError):
    pass


def get_examination(examination_id):
    try:
        parsed_id = int(examination_id)
    except (TypeError, ValueError):
        raise AllocationError(
            "Select a valid examination."
        )

    examination = db.session.get(
        Examination,
        parsed_id,
    )

    if examination is None:
        raise AllocationError(
            "The selected examination does not exist."
        )

    return examination


def get_eligible_students(examination):
    statement = (
        db.select(Student)
        .join(
            StudentEligibility,
            StudentEligibility.student_id
            == Student.id,
        )
        .where(
            StudentEligibility.subject_id
            == examination.subject_id,
            StudentEligibility.eligible.is_(True),
            Student.active.is_(True),
        )
        .order_by(Student.roll_number)
    )

    return db.session.execute(
        statement
    ).scalars().all()


def get_available_seats():
    statement = (
        db.select(Seat)
        .where(Seat.active.is_(True))
        .order_by(
            Seat.room_id,
            Seat.row_code,
            Seat.column_code,
            Seat.seat_code,
        )
    )

    return db.session.execute(
        statement
    ).scalars().all()


def get_adjacency_pairs(valid_seat_ids):
    records = db.session.execute(
        db.select(SeatAdjacency)
    ).scalars().all()

    pairs = set()

    for record in records:
        first_id = record.seat_id
        second_id = record.adjacent_seat_id

        if (
            first_id not in valid_seat_ids
            or second_id not in valid_seat_ids
            or first_id == second_id
        ):
            continue

        pairs.add(
            tuple(sorted((first_id, second_id)))
        )

    return sorted(pairs)


def requires_accessible_seat(student):
    return bool(
        student.special_request
        and student.special_request.strip()
    )


def build_solution(
    students,
    seats,
    adjacency_pairs,
    seed,
):
    if not students:
        raise AllocationError(
            "No eligible students were found "
            "for this examination."
        )

    if len(students) > len(seats):
        shortage = len(students) - len(seats)

        raise AllocationError(
            "Insufficient seating capacity. "
            f"{shortage} additional seats are required. "
            "Nothing was saved."
        )

    accessible_students = [
        student
        for student in students
        if requires_accessible_seat(student)
    ]

    accessible_seats = [
        seat
        for seat in seats
        if seat.accessible
    ]

    if len(accessible_students) > len(accessible_seats):
        shortage = (
            len(accessible_students)
            - len(accessible_seats)
        )

        raise AllocationError(
            "Insufficient accessible seating. "
            f"{shortage} additional accessible seats "
            "are required. Nothing was saved."
        )

    randomizer = random.Random(seed)

    student_order = list(students)
    seat_order = list(seats)

    randomizer.shuffle(student_order)
    randomizer.shuffle(seat_order)

    problem = pulp.LpProblem(
        "examination_seat_allocation",
        pulp.LpMinimize,
    )

    assignments = {
        (student.id, seat.id): pulp.LpVariable(
            f"x_{student.id}_{seat.id}",
            cat="Binary",
        )
        for student in student_order
        for seat in seat_order
    }

    branches = sorted(
        {
            student.branch_id
            for student in student_order
        }
    )

    students_by_branch = {
        branch_id: [
            student
            for student in student_order
            if student.branch_id == branch_id
        ]
        for branch_id in branches
    }

    branch_at_seat = {
        (branch_id, seat.id): pulp.LpVariable(
            f"branch_{branch_id}_{seat.id}",
            cat="Binary",
        )
        for branch_id in branches
        for seat in seat_order
    }

    same_branch_penalties = {
        (branch_id, first_id, second_id):
            pulp.LpVariable(
                "same_"
                f"{branch_id}_{first_id}_{second_id}",
                cat="Binary",
            )
        for branch_id in branches
        for first_id, second_id in adjacency_pairs
    }

    for student in student_order:
        problem += (
            pulp.lpSum(
                assignments[
                    (student.id, seat.id)
                ]
                for seat in seat_order
            )
            == 1
        )

    for seat in seat_order:
        problem += (
            pulp.lpSum(
                assignments[
                    (student.id, seat.id)
                ]
                for student in student_order
            )
            <= 1
        )

    inaccessible_seat_ids = {
        seat.id
        for seat in seat_order
        if not seat.accessible
    }

    for student in accessible_students:
        for seat_id in inaccessible_seat_ids:
            problem += (
                assignments[
                    (student.id, seat_id)
                ]
                == 0
            )

    for branch_id in branches:
        branch_students = students_by_branch[
            branch_id
        ]

        for seat in seat_order:
            problem += (
                branch_at_seat[
                    (branch_id, seat.id)
                ]
                == pulp.lpSum(
                    assignments[
                        (student.id, seat.id)
                    ]
                    for student in branch_students
                )
            )

    for branch_id in branches:
        for first_id, second_id in adjacency_pairs:
            penalty = same_branch_penalties[
                (
                    branch_id,
                    first_id,
                    second_id,
                )
            ]

            problem += (
                penalty
                >= branch_at_seat[
                    (branch_id, first_id)
                ]
                + branch_at_seat[
                    (branch_id, second_id)
                ]
                - 1
            )

    tie_break_cost = []

    for student_position, student in enumerate(
        student_order
    ):
        for seat_position, seat in enumerate(
            seat_order
        ):
            cost = (
                (
                    student_position
                    + seat_position
                    + seed
                )
                % 97
            ) / 10000

            tie_break_cost.append(
                cost
                * assignments[
                    (student.id, seat.id)
                ]
            )

    problem += (
        1000
        * pulp.lpSum(
            same_branch_penalties.values()
        )
        + pulp.lpSum(tie_break_cost)
    )

    solver = pulp.PULP_CBC_CMD(
        msg=False,
        threads=1,
        timeLimit=120,
    )

    status = problem.solve(solver)

    if pulp.LpStatus[status] != "Optimal":
        raise AllocationError(
            "A valid seating plan could not be found. "
            "Nothing was saved."
        )

    solution = []

    for student in student_order:
        assigned_seats = [
            seat
            for seat in seat_order
            if pulp.value(
                assignments[
                    (student.id, seat.id)
                ]
            )
            > 0.5
        ]

        if len(assigned_seats) != 1:
            raise AllocationError(
                "The generated solution failed validation. "
                "Nothing was saved."
            )

        solution.append(
            (student, assigned_seats[0])
        )

    return solution


def validate_solution(
    students,
    solution,
):
    if len(solution) != len(students):
        raise AllocationError(
            "Not every eligible student received a seat."
        )

    student_ids = [
        student.id
        for student, seat in solution
    ]

    seat_ids = [
        seat.id
        for student, seat in solution
    ]

    if len(student_ids) != len(set(student_ids)):
        raise AllocationError(
            "A student was allocated more than once."
        )

    if len(seat_ids) != len(set(seat_ids)):
        raise AllocationError(
            "A seat was allocated more than once."
        )

    for student, seat in solution:
        if (
            requires_accessible_seat(student)
            and not seat.accessible
        ):
            raise AllocationError(
                "An accessibility request was assigned "
                "to an unsuitable seat."
            )


def allocate_examination(
    examination_id,
    regenerate=False,
):
    examination = get_examination(
        examination_id
    )

    existing_run = db.session.scalar(
        db.select(AllocationRun).where(
            AllocationRun.examination_id
            == examination.id
        )
    )

    if existing_run and not regenerate:
        return existing_run

    seed = 1

    if existing_run:
        seed = existing_run.seed + 1

    students = get_eligible_students(
        examination
    )

    seats = get_available_seats()

    adjacency_pairs = get_adjacency_pairs(
        {seat.id for seat in seats}
    )

    solution = build_solution(
        students,
        seats,
        adjacency_pairs,
        seed,
    )

    validate_solution(
        students,
        solution,
    )

    try:
        if existing_run:
            db.session.delete(existing_run)
            db.session.flush()

        allocation_run = AllocationRun(
            examination=examination,
            seed=seed,
            status="completed",
        )

        db.session.add(allocation_run)
        db.session.flush()

        for student, seat in solution:
            db.session.add(
                SeatAllocation(
                    allocation_run=allocation_run,
                    examination=examination,
                    student=student,
                    seat=seat,
                )
            )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return allocation_run


def get_allocation_view(examination_id):
    if examination_id in (None, ""):
        return {
            "examination": None,
            "allocation_run": None,
            "allocations": [],
        }

    examination = get_examination(
        examination_id
    )

    allocation_run = db.session.scalar(
        db.select(AllocationRun).where(
            AllocationRun.examination_id
            == examination.id
        )
    )

    allocations = []

    if allocation_run:
        allocations = db.session.execute(
            db.select(SeatAllocation)
            .where(
                SeatAllocation.allocation_run_id
                == allocation_run.id
            )
            .join(SeatAllocation.seat)
            .order_by(
                Seat.room_id,
                Seat.row_code,
                Seat.column_code,
                Seat.seat_code,
            )
        ).scalars().all()

    return {
        "examination": examination,
        "allocation_run": allocation_run,
        "allocations": allocations,
    }


def swap_allocations(
    first_allocation_id,
    second_allocation_id,
):
    try:
        first_id = int(first_allocation_id)
        second_id = int(second_allocation_id)
    except (TypeError, ValueError):
        raise AllocationError(
            "Select two valid allocations."
        )

    if first_id == second_id:
        raise AllocationError(
            "Select two different students."
        )

    first = db.session.get(
        SeatAllocation,
        first_id,
    )

    second = db.session.get(
        SeatAllocation,
        second_id,
    )

    if first is None or second is None:
        raise AllocationError(
            "One of the selected allocations "
            "does not exist."
        )

    if (
        first.examination_id
        != second.examination_id
    ):
        raise AllocationError(
            "Seats can only be swapped within "
            "the same examination."
        )

    first_student = first.student
    second_student = second.student
    first_seat = first.seat
    second_seat = second.seat
    allocation_run = first.allocation_run
    examination = first.examination

    if (
        requires_accessible_seat(first_student)
        and not second_seat.accessible
    ):
        raise AllocationError(
            f"{first_student.roll_number} requires "
            "an accessible seat."
        )

    if (
        requires_accessible_seat(second_student)
        and not first_seat.accessible
    ):
        raise AllocationError(
            f"{second_student.roll_number} requires "
            "an accessible seat."
        )

    try:
        db.session.delete(first)
        db.session.delete(second)
        db.session.flush()

        db.session.add(
            SeatAllocation(
                allocation_run=allocation_run,
                examination=examination,
                student=first_student,
                seat=second_seat,
                manually_adjusted=True,
            )
        )

        db.session.add(
            SeatAllocation(
                allocation_run=allocation_run,
                examination=examination,
                student=second_student,
                seat=first_seat,
                manually_adjusted=True,
            )
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return examination.id