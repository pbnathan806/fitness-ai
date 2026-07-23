"""session notes and attendance enhancements

Revision ID: 71fd65da5771
Revises: f638630c2dbe
Create Date: 2026-07-23 13:08:25.683338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71fd65da5771'
down_revision: Union[str, None] = 'f638630c2dbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('trainer_feedback', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('homework', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('next_session_focus', sa.Text(), nullable=True))
    op.drop_column('sessions', 'client_notes')

    # New values only append to the existing native enum type; already-stored
    # rows and their order are untouched. Skipping ADD VALUE ... IF NOT EXISTS
    # here would fail if this migration were ever re-run against a partially
    # migrated database, so guard both additions.
    op.execute("ALTER TYPE session_attendance_status ADD VALUE IF NOT EXISTS 'LATE'")
    op.execute("ALTER TYPE session_attendance_status ADD VALUE IF NOT EXISTS 'RESCHEDULED'")


def downgrade() -> None:
    op.add_column('sessions', sa.Column('client_notes', sa.Text(), nullable=True))
    op.drop_column('sessions', 'next_session_focus')
    op.drop_column('sessions', 'homework')
    op.drop_column('sessions', 'trainer_feedback')

    # Postgres has no ALTER TYPE ... DROP VALUE, so reverting the enum
    # requires swapping in a freshly created type with the original values.
    op.execute("ALTER TYPE session_attendance_status RENAME TO session_attendance_status_old")
    op.execute(
        "CREATE TYPE session_attendance_status AS ENUM "
        "('PRESENT', 'CLIENT_NO_SHOW', 'TRAINER_NO_SHOW', 'BOTH_PRESENT')"
    )
    op.execute(
        "ALTER TABLE sessions ALTER COLUMN attendance_status "
        "TYPE session_attendance_status "
        "USING attendance_status::text::session_attendance_status"
    )
    op.execute("DROP TYPE session_attendance_status_old")
