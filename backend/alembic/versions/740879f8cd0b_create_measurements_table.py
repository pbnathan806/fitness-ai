"""create measurements table

Revision ID: 740879f8cd0b
Revises: 71fd65da5771
Create Date: 2026-07-23 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '740879f8cd0b'
down_revision: Union[str, None] = '71fd65da5771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('measurements',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('weight_kg', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('body_fat_percentage', sa.Numeric(precision=4, scale=1), nullable=True),
    sa.Column('chest_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('waist_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('hips_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('left_arm_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('right_arm_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('left_thigh_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('right_thigh_cm', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('resting_heart_rate', sa.Integer(), nullable=True),
    sa.Column('recorded_by', sa.UUID(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('measurements')
