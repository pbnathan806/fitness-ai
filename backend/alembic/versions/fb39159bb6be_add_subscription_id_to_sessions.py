"""add subscription_id to sessions

Revision ID: fb39159bb6be
Revises: 6ac62c3b8776
Create Date: 2026-07-28 14:24:30.913451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb39159bb6be'
down_revision: Union[str, None] = '6ac62c3b8776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('subscription_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'sessions_subscription_id_fkey',
        'sessions', 'subscriptions',
        ['subscription_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('sessions_subscription_id_fkey', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'subscription_id')
