from app.extensions import db


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    students = db.relationship("Student", back_populates="branch")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(
    db.String(50),
    nullable=False,
    unique=True,
)
    name = db.Column(db.String(150), nullable=False)
    branch_id = db.Column(
        db.Integer,
        db.ForeignKey("branches.id"),
        nullable=False,
    )

    branch = db.relationship("Branch", back_populates="students")
class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(
    db.String(50),
    nullable=False,
    unique=True,
)
    rows = db.Column(db.Integer, nullable=False)
    columns = db.Column(db.Integer, nullable=False)
    students_per_desk = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    @property
    def capacity(self):
        return self.rows * self.columns * self.students_per_desk