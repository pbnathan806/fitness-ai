"""seed subscription plan currencies setting

Revision ID: 6ac62c3b8776
Revises: 05ef0559e917
Create Date: 2026-07-28 06:55:21.653447

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ac62c3b8776'
down_revision: Union[str, None] = '05ef0559e917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SETTING_KEY = "subscription_plan_currencies"

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
                "value": "INR,USD",
                "description": (
                    "Comma-separated currency codes offered in the Currency "
                    "dropdown when creating or editing a subscription plan."
                ),
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        application_settings_table.delete().where(
            application_settings_table.c.key == SETTING_KEY
        )
    )
