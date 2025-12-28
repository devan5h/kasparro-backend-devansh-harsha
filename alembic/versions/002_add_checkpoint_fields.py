"""Add checkpoint fields for incremental ingestion

Revision ID: 002_add_checkpoint
Revises: 001_initial
Create Date: 2025-12-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_checkpoint'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to etl_checkpoints table
    op.add_column('etl_checkpoints', sa.Column('last_successful_timestamp', sa.DateTime(), nullable=True))
    op.add_column('etl_checkpoints', sa.Column('last_run_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint for last_run_id
    op.create_foreign_key(
        'fk_checkpoint_run_id',
        'etl_checkpoints',
        'etl_runs',
        ['last_run_id'],
        ['id']
    )
    
    # Make source_name unique (if not already)
    # Note: This might fail if duplicates exist, but the index should already enforce uniqueness
    try:
        op.create_unique_constraint('uq_checkpoints_source', 'etl_checkpoints', ['source_name'])
    except Exception:
        # Constraint might already exist
        pass


def downgrade() -> None:
    # Remove foreign key
    op.drop_constraint('fk_checkpoint_run_id', 'etl_checkpoints', type_='foreignkey')
    
    # Remove columns
    op.drop_column('etl_checkpoints', 'last_run_id')
    op.drop_column('etl_checkpoints', 'last_successful_timestamp')
    
    # Note: We don't drop the unique constraint as it might have existed before

