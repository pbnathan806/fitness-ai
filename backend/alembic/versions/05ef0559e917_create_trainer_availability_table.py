"""create trainer availability table

Revision ID: 05ef0559e917
Revises: 9addc9f58cb7
Create Date: 2026-07-27 21:40:12.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05ef0559e917'
down_revision: Union[str, None] = '9addc9f58cb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('trainer_availability',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('trainer_id', sa.UUID(), nullable=False),
    sa.Column('weekday', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['trainer_id'], ['trainer_profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_availability_trainer', 'trainer_availability', ['trainer_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_availability_trainer', table_name='trainer_availability')
    op.drop_table('trainer_availability')
