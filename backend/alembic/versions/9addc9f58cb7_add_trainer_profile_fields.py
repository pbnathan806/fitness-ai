"""add trainer profile fields

Revision ID: 9addc9f58cb7
Revises: dd617a9bfa18
Create Date: 2026-07-27 21:36:33.653003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9addc9f58cb7'
down_revision: Union[str, None] = 'dd617a9bfa18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trainer_profiles', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('trainer_profiles', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('trainer_profiles', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('trainer_profiles', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True))


def downgrade() -> None:
    op.drop_column('trainer_profiles', 'is_active')
    op.drop_column('trainer_profiles', 'phone_number')
    op.drop_column('trainer_profiles', 'last_name')
    op.drop_column('trainer_profiles', 'first_name')
