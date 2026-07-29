"""seed check_in_edit_window_days application setting

Revision ID: 7b1d6876f2ed
Revises: 9a52c3ea7364
Create Date: 2026-07-29 00:10:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b1d6876f2ed'
down_revision: Union[str, None] = '9a52c3ea7364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SETTING_KEY = "check_in_edit_window_days"
SETTING_VALUE = "30"
SETTING_DESCRIPTION = (
    "Number of days after Session.scheduled_start during which a Check-in "
    "remains editable by CLIENT/TRAINER/SUPER_ADMIN."
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
