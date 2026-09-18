"""Add eligibility criteria.

Revision ID: 32365d4fbdae
Revises: a96e03d61b7f
Create Date: 2026-09-18 17:29:38.952355
"""

from alembic import op
import sqlalchemy as sa


revision = "32365d4fbdae"
down_revision = "a96e03d61b7f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "student_eligibilities",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "attendance_percentage",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "ppt_marks",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "assignment_marks",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "ct1_marks",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "ct2_marks",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "semester_fee_paid",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table(
        "student_eligibilities",
        schema=None,
    ) as batch_op:
        batch_op.drop_column("semester_fee_paid")
        batch_op.drop_column("ct2_marks")
        batch_op.drop_column("ct1_marks")
        batch_op.drop_column("assignment_marks")
        batch_op.drop_column("ppt_marks")
        batch_op.drop_column("attendance_percentage")