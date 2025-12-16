"""Add deduplication and versioning for Option 1+ (Smart Caching)

Revision ID: 005_dedupe_version
Revises: 004
Create Date: 2025-11-17

This migration implements Option 1+ architecture:
- Request deduplication via hash to prevent duplicate calculations
- Result versioning to track calculation history (keep last 5)
- Smart cache expiry based on data source freshness
- Popularity tracking for analytics

Changes:
1. job_pricing_requests:
   - Add request_hash for deduplication
   - Add first_requested_at, last_requested_at for tracking
   - Add request_count for popularity analytics

2. job_pricing_results:
   - Add version, is_latest for versioning
   - Add calculated_at, expires_at for smart caching
   - Add cache_hit for analytics
   - Remove uq_result_request unique constraint
   - Add uq_request_version (request_id, version)
   - Add partial unique index on (request_id, is_latest) WHERE is_latest = TRUE
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_dedupe_version'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deduplication and versioning fields"""

    # ========================================================================
    # Part 1: Update job_pricing_requests for deduplication
    # ========================================================================

    print("Adding deduplication fields to job_pricing_requests...")

    # Add deduplication columns
    op.add_column('job_pricing_requests',
        sa.Column('request_hash', sa.String(length=64), nullable=True,
                  comment="SHA256 hash of (job_title + location + user_id) for deduplication"))

    op.add_column('job_pricing_requests',
        sa.Column('first_requested_at', sa.DateTime(timezone=True), nullable=True,
                  server_default=sa.text('NOW()'),
                  comment="First time this unique job combination was requested"))

    op.add_column('job_pricing_requests',
        sa.Column('last_requested_at', sa.DateTime(timezone=True), nullable=True,
                  server_default=sa.text('NOW()'),
                  comment="Most recent time this job was requested"))

    op.add_column('job_pricing_requests',
        sa.Column('request_count', sa.Integer(), nullable=False,
                  server_default=sa.text('1'),
                  comment="Number of times this job has been requested (tracks popularity)"))

    # Create unique index on request_hash
    op.create_index('idx_request_hash', 'job_pricing_requests', ['request_hash'], unique=True)

    # Backfill request_hash for existing rows using MD5 (good enough for deduplication)
    op.execute("""
        UPDATE job_pricing_requests
        SET request_hash = MD5(
            LOWER(COALESCE(job_title, '')) || '|' ||
            LOWER(COALESCE(location_text, '')) || '|' ||
            COALESCE(requested_by, '')
        )
        WHERE request_hash IS NULL
    """)

    print("Deduplication fields added successfully")

    # ========================================================================
    # Part 2: Update job_pricing_results for versioning
    # ========================================================================

    print("Adding versioning fields to job_pricing_results...")

    # Add versioning columns
    op.add_column('job_pricing_results',
        sa.Column('version', sa.Integer(), nullable=False,
                  server_default=sa.text('1'),
                  comment="Version number for this request (increments on recalculation)"))

    op.add_column('job_pricing_results',
        sa.Column('is_latest', sa.Boolean(), nullable=False,
                  server_default=sa.text('TRUE'),
                  comment="True if this is the latest version for this request"))

    op.add_column('job_pricing_results',
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'),
                  comment="Timestamp when salary was calculated"))

    op.add_column('job_pricing_results',
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW() + INTERVAL '24 hours'"),
                  comment="Cache expiry timestamp (smart TTL based on data sources)"))

    op.add_column('job_pricing_results',
        sa.Column('cache_hit', sa.Boolean(), nullable=False,
                  server_default=sa.text('FALSE'),
                  comment="True if this result was served from cache (for analytics)"))

    # Create indexes for versioning
    op.create_index('idx_pricing_results_is_latest', 'job_pricing_results', ['is_latest'])
    op.create_index('idx_pricing_results_expires', 'job_pricing_results', ['expires_at'])

    print("Versioning fields added successfully")

    # ========================================================================
    # Part 3: Update constraints for versioning
    # ========================================================================

    print("Updating constraints for versioning...")

    # Drop old unique constraint (request_id)
    op.drop_constraint('uq_result_request', 'job_pricing_results', type_='unique')

    # Add new unique constraint (request_id, version)
    op.create_unique_constraint('uq_request_version', 'job_pricing_results',
                               ['request_id', 'version'])

    # Add partial unique index: only one latest result per request
    # Note: SQLAlchemy/Alembic doesn't directly support partial indexes in create_index
    # We need to execute raw SQL for PostgreSQL-specific partial index
    op.execute("""
        CREATE UNIQUE INDEX idx_latest_result
        ON job_pricing_results(request_id, is_latest)
        WHERE is_latest = TRUE
    """)

    print("Constraints updated successfully")

    # ========================================================================
    # Part 4: Backfill calculated_at from created_at
    # ========================================================================

    print("Backfilling calculated_at from created_at...")

    op.execute("""
        UPDATE job_pricing_results
        SET calculated_at = created_at
        WHERE calculated_at IS NULL
    """)

    print("Migration completed successfully!")


def downgrade() -> None:
    """Revert deduplication and versioning changes"""

    print("Reverting deduplication and versioning changes...")

    # ========================================================================
    # Part 1: Revert job_pricing_results changes
    # ========================================================================

    # Drop partial unique index
    op.drop_index('idx_latest_result', 'job_pricing_results')

    # Drop new unique constraint
    op.drop_constraint('uq_request_version', 'job_pricing_results', type_='unique')

    # Restore old unique constraint
    op.create_unique_constraint('uq_result_request', 'job_pricing_results', ['request_id'])

    # Drop versioning indexes
    op.drop_index('idx_pricing_results_expires', 'job_pricing_results')
    op.drop_index('idx_pricing_results_is_latest', 'job_pricing_results')

    # Drop versioning columns
    op.drop_column('job_pricing_results', 'cache_hit')
    op.drop_column('job_pricing_results', 'expires_at')
    op.drop_column('job_pricing_results', 'calculated_at')
    op.drop_column('job_pricing_results', 'is_latest')
    op.drop_column('job_pricing_results', 'version')

    # ========================================================================
    # Part 2: Revert job_pricing_requests changes
    # ========================================================================

    # Drop deduplication index
    op.drop_index('idx_request_hash', 'job_pricing_requests')

    # Drop deduplication columns
    op.drop_column('job_pricing_requests', 'request_count')
    op.drop_column('job_pricing_requests', 'last_requested_at')
    op.drop_column('job_pricing_requests', 'first_requested_at')
    op.drop_column('job_pricing_requests', 'request_hash')

    print("Downgrade completed successfully")
