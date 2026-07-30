"""seed measurement edit window days setting

Revision ID: 71576b567d85
Revises: 7b1d6876f2ed
Create Date: 2026-07-30 06:32:38.340786

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71576b567d85'
down_revision: Union[str, None] = '7b1d6876f2ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SETTING_KEY = "measurement_edit_window_days"
SETTING_VALUE = "30"
SETTING_DESCRIPTION = (
    "Number of days after Measurement.recorded_at during which a measurement "
    "remains editable by TRAINER/SUPER_ADMIN."
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
