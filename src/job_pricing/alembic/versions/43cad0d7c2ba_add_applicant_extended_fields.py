"""add_applicant_extended_fields

Revision ID: 43cad0d7c2ba
Revises: 002_add_tpc_fields
Create Date: 2025-11-13 07:14:58.249956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43cad0d7c2ba'
down_revision: Union[str, None] = '002_add_tpc_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to applicants table
    op.add_column('applicants', sa.Column('name', sa.String(length=200), nullable=True))
    op.add_column('applicants', sa.Column('current_organisation', sa.String(length=200), nullable=True))
    op.add_column('applicants', sa.Column('current_title', sa.String(length=200), nullable=True))
    op.add_column('applicants', sa.Column('organisation_summary', sa.Text(), nullable=True))
    op.add_column('applicants', sa.Column('role_scope', sa.Text(), nullable=True))
    op.add_column('applicants', sa.Column('application_year', sa.String(length=4), nullable=True))
    op.add_column('applicants', sa.Column('sharepoint_file_id', sa.String(length=255), nullable=True))
    op.add_column('applicants', sa.Column('last_updated', sa.TIMESTAMP(timezone=True), nullable=True))

    # Drop old check constraint
    op.drop_constraint('check_application_status', 'applicants', type_='check')

    # Add updated check constraint with new statuses
    op.create_check_constraint(
        'check_application_status',
        'applicants',
        "application_status IN ('Applied', 'Shortlisted', 'Interview Stage 1', 'Interview Stage 2', 'Interviewed', 'Offer Extended', 'Offered', 'Declined Offer', 'Rejected', 'Withdrawn', 'Hired')"
    )

    # Add indexes
    op.create_index('idx_applicants_year', 'applicants', ['application_year'], unique=False)
    op.create_index('idx_applicants_organisation', 'applicants', ['current_organisation'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_applicants_organisation', table_name='applicants')
    op.drop_index('idx_applicants_year', table_name='applicants')

    # Revert check constraint
    op.drop_constraint('check_application_status', 'applicants', type_='check')
    op.create_check_constraint(
        'check_application_status',
        'applicants',
        "application_status IN ('Applied', 'Shortlisted', 'Interviewed', 'Offered', 'Rejected', 'Withdrawn')"
    )

    # Drop columns
    op.drop_column('applicants', 'last_updated')
    op.drop_column('applicants', 'sharepoint_file_id')
    op.drop_column('applicants', 'application_year')
    op.drop_column('applicants', 'role_scope')
    op.drop_column('applicants', 'organisation_summary')
    op.drop_column('applicants', 'current_title')
    op.drop_column('applicants', 'current_organisation')
    op.drop_column('applicants', 'name')
