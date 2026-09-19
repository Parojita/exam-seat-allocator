from app.extensions import db


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    students = db.relationship(
        "Student",
        back_populates="branch",
    )

    subjects = db.relationship(
        "Subject",
        back_populates="branch",
    )


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    roll_number = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    branch_id = db.Column(
        db.Integer,
        db.ForeignKey("branches.id"),
        nullable=False,
    )

    semester = db.Column(
        db.Integer,
        nullable=True,
    )

    email = db.Column(
        db.String(150),
        nullable=True,
    )

    photo_path = db.Column(
        db.String(255),
        nullable=True,
    )

    special_request = db.Column(
        db.String(255),
        nullable=True,
    )

    rfid_uid = db.Column(
        db.String(100),
        nullable=True,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    branch = db.relationship(
        "Branch",
        back_populates="students",
    )


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)

    subject_code = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    branch_id = db.Column(
        db.Integer,
        db.ForeignKey("branches.id"),
        nullable=False,
    )

    semester = db.Column(
        db.Integer,
        nullable=False,
    )

    exam_type = db.Column(
        db.String(20),
        nullable=False,
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    branch = db.relationship(
        "Branch",
        back_populates="subjects",
    )


class StudentEligibility(db.Model):
    __tablename__ = "student_eligibilities"

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "subject_id",
            name="uq_student_subject_eligibility",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
    )
    attendance_percentage = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    ppt_marks = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    assignment_marks = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    ct1_marks = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    ct2_marks = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    semester_fee_paid = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )
    eligible = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    student = db.relationship("Student")
    subject = db.relationship("Subject")


class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)

    exam_code = db.Column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
    )

    exam_date = db.Column(
        db.Date,
        nullable=False,
    )

    start_time = db.Column(
        db.Time,
        nullable=False,
    )

    end_time = db.Column(
        db.Time,
        nullable=False,
    )

    exam_type = db.Column(
        db.String(20),
        nullable=False,
    )

    subject = db.relationship("Subject")


class Faculty(db.Model):
    __tablename__ = "faculties"

    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    department = db.Column(
        db.String(50),
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        nullable=False,
    )

    max_duties = db.Column(
        db.Integer,
        nullable=False,
    )


class FacultySubject(db.Model):
    __tablename__ = "faculty_subjects"

    __table_args__ = (
        db.UniqueConstraint(
            "faculty_id",
            "subject_id",
            name="uq_faculty_subject",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculties.id"),
        nullable=False,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
    )

    faculty = db.relationship("Faculty")
    subject = db.relationship("Subject")


class FacultyAvailability(db.Model):
    __tablename__ = "faculty_availability"

    __table_args__ = (
        db.UniqueConstraint(
            "faculty_id",
            "date",
            "session",
            name="uq_faculty_date_session",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculties.id"),
        nullable=False,
    )

    date = db.Column(
        db.Date,
        nullable=False,
    )

    session = db.Column(
        db.String(30),
        nullable=False,
    )

    available = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    faculty = db.relationship("Faculty")


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)

    room_number = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
    )

    building = db.Column(
        db.String(100),
        nullable=True,
    )

    floor = db.Column(
        db.Integer,
        nullable=True,
    )

    official_capacity = db.Column(
        db.Integer,
        nullable=True,
    )

    exam_capacity = db.Column(
        db.Integer,
        nullable=True,
    )

    room_type = db.Column(
        db.String(50),
        nullable=True,
    )

    rows = db.Column(
        db.Integer,
        nullable=True,
    )

    columns = db.Column(
        db.Integer,
        nullable=True,
    )

    students_per_desk = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    seats = db.relationship(
        "Seat",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    @property
    def capacity(self):
        if self.exam_capacity is not None:
            return self.exam_capacity

        if self.rows is None or self.columns is None:
            return 0

        return self.rows * self.columns * self.students_per_desk


class Seat(db.Model):
    __tablename__ = "seats"

    __table_args__ = (
        db.UniqueConstraint(
            "room_id",
            "seat_code",
            name="uq_room_seat_code",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("rooms.id"),
        nullable=False,
    )

    desk_code = db.Column(
        db.String(50),
        nullable=False,
    )

    seat_code = db.Column(
        db.String(50),
        nullable=False,
    )

    row_code = db.Column(
        db.String(50),
        nullable=True,
    )

    column_code = db.Column(
        db.String(50),
        nullable=True,
    )

    accessible = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    room = db.relationship(
        "Room",
        back_populates="seats",
    )

    @property
    def label(self):
        return self.seat_code


class SeatAdjacency(db.Model):
    __tablename__ = "seat_adjacencies"

    __table_args__ = (
        db.UniqueConstraint(
            "seat_id",
            "adjacent_seat_id",
            name="uq_seat_adjacency_pair",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id"),
        nullable=False,
    )

    adjacent_seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id"),
        nullable=False,
    )

    seat = db.relationship(
        "Seat",
        foreign_keys=[seat_id],
    )

    adjacent_seat = db.relationship(
        "Seat",
        foreign_keys=[adjacent_seat_id],
    )
class AllocationRun(db.Model):
    __tablename__ = "allocation_runs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False,
        unique=True,
    )

    seed = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="completed",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    examination = db.relationship(
        "Examination",
    )

    allocations = db.relationship(
        "SeatAllocation",
        back_populates="allocation_run",
        cascade="all, delete-orphan",
    )


class SeatAllocation(db.Model):
    __tablename__ = "seat_allocations"

    __table_args__ = (
        db.UniqueConstraint(
            "examination_id",
            "student_id",
            name="uq_exam_student_allocation",
        ),
        db.UniqueConstraint(
            "examination_id",
            "seat_id",
            name="uq_exam_seat_allocation",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    allocation_run_id = db.Column(
        db.Integer,
        db.ForeignKey("allocation_runs.id"),
        nullable=False,
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False,
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False,
    )

    seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id"),
        nullable=False,
    )

    manually_adjusted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    allocation_run = db.relationship(
        "AllocationRun",
        back_populates="allocations",
    )

    examination = db.relationship(
        "Examination",
    )

    student = db.relationship(
        "Student",
    )

    seat = db.relationship(
        "Seat",
    )


class InvigilatorDuty(db.Model):
    __tablename__ = "invigilator_duties"

    __table_args__ = (
        db.UniqueConstraint(
            "examination_id",
            "room_id",
            name="uq_exam_room_invigilator",
        ),
        db.UniqueConstraint(
            "examination_id",
            "faculty_id",
            name="uq_exam_faculty_invigilator",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False,
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("rooms.id"),
        nullable=False,
    )

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculties.id"),
        nullable=False,
    )

    examination = db.relationship(
        "Examination",
    )

    room = db.relationship(
        "Room",
    )

    faculty = db.relationship(
        "Faculty",
    )