"""create check_ins table

Revision ID: 8ff2a6e4d843
Revises: 740879f8cd0b
Create Date: 2026-07-23 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ff2a6e4d843'
down_revision: Union[str, None] = '740879f8cd0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('check_ins',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('sleep_hours', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('water_intake_liters', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('energy_level', sa.Integer(), nullable=True),
    sa.Column('mood', sa.Integer(), nullable=True),
    sa.Column('workout_completed', sa.Boolean(), nullable=True),
    sa.Column('diet_followed', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('submitted_by', sa.UUID(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('check_ins')
