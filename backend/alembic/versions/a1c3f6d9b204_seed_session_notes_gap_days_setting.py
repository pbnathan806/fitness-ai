"""seed session_notes_gap_days application setting

Revision ID: a1c3f6d9b204
Revises: 862fb85e1618
Create Date: 2026-08-08 09:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3f6d9b204'
down_revision: Union[str, None] = '862fb85e1618'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SETTING_KEY = "session_notes_gap_days"
SETTING_VALUE = "2"
SETTING_DESCRIPTION = (
    "Number of trailing days (including today, Asia/Kolkata) checked for a "
    "Trainer's past sessions missing trainer_notes, surfaced on the Trainer "
    "Dashboard's Session Notes Gap widget."
)

application_settings_table = sa.table(
    "application_settings",
    sa.column("id", sa.UUID()),
    sa.column("key", sa.String()),
    sa.column("value", sa.Text()),
    sa.column("description", sa.Text()),
)


def upgrade() -> None:
    op.bulk_insert(
        application_settings_table,
        [
            {
                "id": uuid.uuid4(),
                "key": SETTING_KEY,
                "value": SETTING_VALUE,
                "description": SETTING_DESCRIPTION,
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        application_settings_table.delete().where(
            application_settings_table.c.key == SETTING_KEY
        )
    )
