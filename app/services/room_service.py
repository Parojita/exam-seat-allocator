from app.extensions import db
from app.models import Room, Seat


class RoomValidationError(ValueError):
    pass


def clean_optional_text(value):
    if value is None:
        return None

    cleaned_value = str(value).strip()

    if cleaned_value == "":
        return None

    return cleaned_value


def parse_integer(value, error_message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise RoomValidationError(
            error_message
        ) from None


def create_room_with_seats(form_data):
    room_number = str(
        form_data.get("room_number", "")
    ).strip()

    if room_number == "":
        raise RoomValidationError(
            "Room number is required."
        )

    rows = parse_integer(
        form_data.get("rows"),
        "Rows must be a whole number.",
    )

    if rows < 1 or rows > 26:
        raise RoomValidationError(
            "Rows must be between 1 and 26."
        )

    columns = parse_integer(
        form_data.get("columns"),
        "Columns must be a whole number.",
    )

    if columns < 1 or columns > 100:
        raise RoomValidationError(
            "Columns must be between 1 and 100."
        )

    floor_value = form_data.get("floor")

    if (
        floor_value is None
        or str(floor_value).strip() == ""
    ):
        floor = None
    else:
        floor = parse_integer(
            floor_value,
            "Floor must be a whole number.",
        )

    existing_room = db.session.scalar(
        db.select(Room).where(
            db.func.lower(Room.room_number)
            == room_number.casefold()
        )
    )

    if existing_room is not None:
        raise RoomValidationError(
            "A room with this room number "
            "already exists."
        )

    capacity = rows * columns

    room = Room(
        room_number=room_number,
        building=clean_optional_text(
            form_data.get("building")
        ),
        floor=floor,
        official_capacity=capacity,
        exam_capacity=capacity,
        room_type=clean_optional_text(
            form_data.get("room_type")
        ),
        rows=rows,
        columns=columns,
        students_per_desk=1,
    )

    try:
        db.session.add(room)
        db.session.flush()

        for row_index in range(rows):
            row_code = chr(
                ord("A") + row_index
            )

            for column_number in range(
                1,
                columns + 1,
            ):
                column_code = str(
                    column_number
                )

                seat_code = (
                    f"{row_code}{column_code}"
                )

                seat = Seat(
                    room=room,
                    desk_code=seat_code,
                    seat_code=seat_code,
                    row_code=row_code,
                    column_code=column_code,
                    accessible=False,
                    active=True,
                )

                db.session.add(seat)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return room