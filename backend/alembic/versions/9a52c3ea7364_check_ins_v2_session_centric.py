"""check-ins v2: session-centric refactor

Revision ID: 9a52c3ea7364
Revises: fb39159bb6be
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a52c3ea7364'
down_revision: Union[str, None] = 'fb39159bb6be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MVP app with no production data: no existing check_ins rows need
    # backfilling, so session_id can be added directly as NOT NULL + UNIQUE.
    op.add_column('check_ins', sa.Column('session_id', sa.UUID(), nullable=False))
    op.create_foreign_key(
        'check_ins_session_id_fkey',
        'check_ins', 'sessions',
        ['session_id'], ['id'],
    )
    op.create_unique_constraint('uq_check_ins_session_id', 'check_ins', ['session_id'])


def downgrade() -> None:
    op.drop_constraint('uq_check_ins_session_id', 'check_ins', type_='unique')
    op.drop_constraint('check_ins_session_id_fkey', 'check_ins', type_='foreignkey')
    op.drop_column('check_ins', 'session_id')
