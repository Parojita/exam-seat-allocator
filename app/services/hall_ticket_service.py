from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import qrcode
from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.extensions import db
from app.models import SeatAllocation


class HallTicketError(ValueError):
    pass


def get_hall_ticket_record(allocation_id):
    try:
        parsed_id = int(allocation_id)
    except (TypeError, ValueError):
        raise HallTicketError(
            "Select a valid seat allocation."
        )

    allocation = db.session.get(
        SeatAllocation,
        parsed_id,
    )

    if allocation is None:
        raise HallTicketError(
            "The requested hall ticket does not exist."
        )

    return allocation


def create_qr_image(data):
    qr_code = qrcode.make(data)

    qr_buffer = BytesIO()
    qr_code.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    return Image(
        qr_buffer,
        width=32 * mm,
        height=32 * mm,
    )


def find_student_photo(photo_path):
    if not photo_path:
        return None

    candidate = Path(photo_path)

    if not candidate.is_absolute():
        candidate = (
            Path(current_app.root_path)
            / candidate
        )

    if not candidate.is_file():
        return None

    return candidate


def generate_hall_ticket_pdf(
    allocation_id,
    verification_url,
):
    allocation = get_hall_ticket_record(
        allocation_id
    )

    student = allocation.student
    examination = allocation.examination
    subject = examination.subject
    seat = allocation.seat
    room = seat.room

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            f"Hall Ticket - {student.roll_number}"
        ),
        author="Examination Cell",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "HallTicketTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0d6efd"),
        spaceAfter=5 * mm,
    )

    subtitle_style = ParagraphStyle(
        "HallTicketSubtitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )

    label_style = ParagraphStyle(
        "HallTicketLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#495057"),
    )

    value_style = ParagraphStyle(
        "HallTicketValue",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
    )

    note_style = ParagraphStyle(
        "HallTicketNote",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6c757d"),
    )

    story = [
        Paragraph(
            "UNIVERSITY EXAMINATION CELL",
            title_style,
        ),
        Paragraph(
            "OFFICIAL HALL TICKET",
            subtitle_style,
        ),
    ]

    photo_path = find_student_photo(
        student.photo_path
    )

    if photo_path:
        student_photo = Image(
            str(photo_path),
            width=30 * mm,
            height=38 * mm,
        )
    else:
        student_photo = Table(
            [
                [
                    Paragraph(
                        "PHOTO<br/>NOT<br/>AVAILABLE",
                        note_style,
                    )
                ]
            ],
            colWidths=[30 * mm],
            rowHeights=[38 * mm],
        )

        student_photo.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor("#adb5bd"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

    student_details = Table(
        [
            [
                Paragraph(
                    "Student Name",
                    label_style,
                ),
                Paragraph(
                    escape(student.name),
                    value_style,
                ),
            ],
            [
                Paragraph(
                    "Roll Number",
                    label_style,
                ),
                Paragraph(
                    escape(student.roll_number),
                    value_style,
                ),
            ],
            [
                Paragraph(
                    "Branch",
                    label_style,
                ),
                Paragraph(
                    escape(student.branch.code),
                    value_style,
                ),
            ],
            [
                Paragraph(
                    "Semester",
                    label_style,
                ),
                Paragraph(
                    str(student.semester or "-"),
                    value_style,
                ),
            ],
        ],
        colWidths=[32 * mm, 88 * mm],
    )

    student_details.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#ced4da"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#f1f3f5"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    identity_section = Table(
        [[student_photo, student_details]],
        colWidths=[36 * mm, 120 * mm],
    )

    identity_section.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(identity_section)
    story.append(Spacer(1, 7 * mm))

    exam_rows = [
        [
            Paragraph("Exam Code", label_style),
            Paragraph(
                escape(examination.exam_code),
                value_style,
            ),
        ],
        [
            Paragraph("Subject", label_style),
            Paragraph(
                escape(
                    f"{subject.subject_code} - "
                    f"{subject.name}"
                ),
                value_style,
            ),
        ],
        [
            Paragraph("Exam Type", label_style),
            Paragraph(
                escape(examination.exam_type),
                value_style,
            ),
        ],
        [
            Paragraph("Date", label_style),
            Paragraph(
                examination.exam_date.strftime(
                    "%d %B %Y"
                ),
                value_style,
            ),
        ],
        [
            Paragraph("Time", label_style),
            Paragraph(
                examination.start_time.strftime(
                    "%I:%M %p"
                )
                + " - "
                + examination.end_time.strftime(
                    "%I:%M %p"
                ),
                value_style,
            ),
        ],
        [
            Paragraph("Building", label_style),
            Paragraph(
                escape(room.building or "-"),
                value_style,
            ),
        ],
        [
            Paragraph("Room", label_style),
            Paragraph(
                escape(room.room_number),
                value_style,
            ),
        ],
        [
            Paragraph("Seat", label_style),
            Paragraph(
                escape(seat.seat_code),
                value_style,
            ),
        ],
    ]

    exam_table = Table(
        exam_rows,
        colWidths=[40 * mm, 116 * mm],
    )

    exam_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#ced4da"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#e7f1ff"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(exam_table)
    story.append(Spacer(1, 7 * mm))

    qr_image = create_qr_image(
        verification_url
    )

    verification_table = Table(
        [
            [
                qr_image,
                Paragraph(
                    "<b>Verification QR</b><br/>"
                    "Scan this code to verify the "
                    "student's saved examination "
                    "and seating assignment.",
                    value_style,
                ),
            ]
        ],
        colWidths=[40 * mm, 116 * mm],
    )

    verification_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#0d6efd"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(verification_table)
    story.append(Spacer(1, 7 * mm))

    if student.special_request:
        story.append(
            Paragraph(
                "<b>Approved seating accommodation:</b> "
                + escape(student.special_request),
                value_style,
            )
        )

        story.append(Spacer(1, 4 * mm))

    story.append(
        Paragraph(
            "Instructions: Bring this hall ticket and "
            "a valid university identity card. Report "
            "to the assigned room at least 30 minutes "
            "before the examination.",
            note_style,
        )
    )

    document.build(story)

    output.seek(0)

    filename = (
        f"{student.roll_number}_hall_ticket.pdf"
    )

    return output, filename