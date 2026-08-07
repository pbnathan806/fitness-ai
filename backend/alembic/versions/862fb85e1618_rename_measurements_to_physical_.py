"""rename measurements to physical_assessments and add photo columns

Revision ID: 862fb85e1618
Revises: 71576b567d85
Create Date: 2026-08-07 16:18:11.232816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '862fb85e1618'
down_revision: Union[str, None] = '71576b567d85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_OVERDUE_KEY = "measurement_overdue_days"
NEW_OVERDUE_KEY = "physical_assessment_overdue_days"
NEW_OVERDUE_DESCRIPTION = (
    "Number of days after which a client is considered overdue for "
    "physical assessments."
)

OLD_EDIT_WINDOW_KEY = "measurement_edit_window_days"
NEW_EDIT_WINDOW_KEY = "physical_assessment_edit_window_days"
NEW_EDIT_WINDOW_DESCRIPTION = (
    "Number of days after PhysicalAssessment.recorded_at during which a "
    "physical assessment remains editable by TRAINER/SUPER_ADMIN."
)

application_settings_table = sa.table(
    "application_settings",
    sa.column("key", sa.String()),
    sa.column("description", sa.Text()),
)


def upgrade() -> None:
    op.rename_table('measurements', 'physical_assessments')
    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT measurements_pkey "
        "TO physical_assessments_pkey"
    )
    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT "
        "measurements_client_id_fkey TO physical_assessments_client_id_fkey"
    )
    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT "
        "measurements_recorded_by_fkey TO physical_assessments_recorded_by_fkey"
    )

    # Groundwork for a not-yet-built photo upload capability - nullable,
    # storage-provider-agnostic external URL columns. See
    # models/physical_assessment.py for the full rationale.
    op.add_column('physical_assessments', sa.Column('front_photo_url', sa.String(length=2048), nullable=True))
    op.add_column('physical_assessments', sa.Column('back_photo_url', sa.String(length=2048), nullable=True))
    op.add_column('physical_assessments', sa.Column('side_photo_url', sa.String(length=2048), nullable=True))

    op.execute(
        application_settings_table.update()
        .where(application_settings_table.c.key == OLD_OVERDUE_KEY)
        .values(key=NEW_OVERDUE_KEY, description=NEW_OVERDUE_DESCRIPTION)
    )
    op.execute(
        application_settings_table.update()
        .where(application_settings_table.c.key == OLD_EDIT_WINDOW_KEY)
        .values(key=NEW_EDIT_WINDOW_KEY, description=NEW_EDIT_WINDOW_DESCRIPTION)
    )


def downgrade() -> None:
    op.execute(
        application_settings_table.update()
        .where(application_settings_table.c.key == NEW_EDIT_WINDOW_KEY)
        .values(
            key=OLD_EDIT_WINDOW_KEY,
            description=(
                "Number of days after Measurement.recorded_at during which a measurement "
                "remains editable by TRAINER/SUPER_ADMIN."
            ),
        )
    )
    op.execute(
        application_settings_table.update()
        .where(application_settings_table.c.key == NEW_OVERDUE_KEY)
        .values(
            key=OLD_OVERDUE_KEY,
            description=(
                "Number of days after which a client is considered overdue for "
                "measurements."
            ),
        )
    )

    op.drop_column('physical_assessments', 'side_photo_url')
    op.drop_column('physical_assessments', 'back_photo_url')
    op.drop_column('physical_assessments', 'front_photo_url')

    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT "
        "physical_assessments_recorded_by_fkey TO measurements_recorded_by_fkey"
    )
    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT "
        "physical_assessments_client_id_fkey TO measurements_client_id_fkey"
    )
    op.execute(
        "ALTER TABLE physical_assessments RENAME CONSTRAINT physical_assessments_pkey "
        "TO measurements_pkey"
    )
    op.rename_table('physical_assessments', 'measurements')
