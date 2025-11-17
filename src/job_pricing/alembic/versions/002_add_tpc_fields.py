"""Add TPC-specific fields to job_pricing_requests

Revision ID: 002_add_tpc_fields
Revises: 001_initial
Create Date: 2025-11-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_tpc_fields'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add TPC-specific fields to job_pricing_requests table."""
    # Add new columns
    op.add_column('job_pricing_requests',
        sa.Column('portfolio', sa.String(length=255), nullable=True,
                  comment="Portfolio/Entity (e.g., 'TPC Group Corporate Office')"))

    op.add_column('job_pricing_requests',
        sa.Column('department', sa.String(length=255), nullable=True,
                  comment="Department (e.g., 'People & Organisation', 'Finance')"))

    op.add_column('job_pricing_requests',
        sa.Column('employment_type', sa.String(length=50), nullable=True,
                  comment="Employment type (permanent, contract, fixed-term, secondment)"))

    op.add_column('job_pricing_requests',
        sa.Column('job_family', sa.String(length=255), nullable=True,
                  comment="Job family (e.g., 'Total Rewards', 'Finance')"))

    op.add_column('job_pricing_requests',
        sa.Column('alternative_titles', postgresql.ARRAY(sa.Text()), nullable=True,
                  comment="Alternative market titles for broader matching"))

    op.add_column('job_pricing_requests',
        sa.Column('mercer_job_code', sa.String(length=100), nullable=True,
                  comment="Mercer job code (e.g., 'HRM.04.005.M50')"))

    op.add_column('job_pricing_requests',
        sa.Column('mercer_job_description', sa.Text(), nullable=True,
                  comment="Mercer job description/mapping details"))


def downgrade() -> None:
    """Remove TPC-specific fields from job_pricing_requests table."""
    op.drop_column('job_pricing_requests', 'mercer_job_description')
    op.drop_column('job_pricing_requests', 'mercer_job_code')
    op.drop_column('job_pricing_requests', 'alternative_titles')
    op.drop_column('job_pricing_requests', 'job_family')
    op.drop_column('job_pricing_requests', 'employment_type')
    op.drop_column('job_pricing_requests', 'department')
    op.drop_column('job_pricing_requests', 'portfolio')
