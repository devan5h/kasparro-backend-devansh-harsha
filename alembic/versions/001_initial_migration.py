"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Raw data tables
    op.create_table(
        'raw_coinpaprika',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_data', sa.Text(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_raw_coinpaprika_ingested', 'raw_coinpaprika', ['ingested_at'])
    
    op.create_table(
        'raw_coingecko',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_data', sa.Text(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_raw_coingecko_ingested', 'raw_coingecko', ['ingested_at'])
    
    op.create_table(
        'raw_csv',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_data', sa.Text(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_raw_csv_ingested', 'raw_csv', ['ingested_at'])
    
    # Normalized tables
    op.create_table(
        'coins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_coins_symbol_source', 'coins', ['symbol', 'source'], unique=True)
    op.create_index(op.f('ix_coins_symbol'), 'coins', ['symbol'])
    op.create_index(op.f('ix_coins_source'), 'coins', ['source'])
    
    op.create_table(
        'prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('coin_id', sa.Integer(), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('market_cap_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('volume_24h_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['coin_id'], ['coins.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prices_coin_timestamp_source', 'prices', ['coin_id', 'timestamp', 'source'], unique=True)
    op.create_index(op.f('ix_prices_coin_id'), 'prices', ['coin_id'])
    op.create_index(op.f('ix_prices_timestamp'), 'prices', ['timestamp'])
    
    op.create_table(
        'market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('coin_id', sa.Integer(), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('market_cap_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('volume_24h_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('price_change_24h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['coin_id'], ['coins.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_market_data_coin_timestamp_source', 'market_data', ['coin_id', 'timestamp', 'source'], unique=True)
    op.create_index(op.f('ix_market_data_coin_id'), 'market_data', ['coin_id'])
    op.create_index(op.f('ix_market_data_timestamp'), 'market_data', ['timestamp'])
    
    # Metadata tables
    op.create_table(
        'etl_checkpoints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('last_ingested_id', sa.String(length=200), nullable=True),
        sa.Column('last_ingested_timestamp', sa.DateTime(), nullable=True),
        sa.Column('checkpoint_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_checkpoints_source', 'etl_checkpoints', ['source_name'], unique=True)
    op.create_index(op.f('ix_etl_checkpoints_source_name'), 'etl_checkpoints', ['source_name'])
    
    op.create_table(
        'etl_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('RUNNING', 'SUCCESS', 'FAILED', name='etlstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('records_ingested', sa.Integer(), nullable=True),
        sa.Column('records_normalized', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('run_metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_etl_runs_source_status', 'etl_runs', ['source_name', 'status'])
    op.create_index('idx_etl_runs_started', 'etl_runs', ['started_at'])
    op.create_index(op.f('ix_etl_runs_source_name'), 'etl_runs', ['source_name'])
    op.create_index(op.f('ix_etl_runs_status'), 'etl_runs', ['status'])


def downgrade() -> None:
    op.drop_index(op.f('ix_etl_runs_status'), table_name='etl_runs')
    op.drop_index(op.f('ix_etl_runs_source_name'), table_name='etl_runs')
    op.drop_index('idx_etl_runs_started', table_name='etl_runs')
    op.drop_index('idx_etl_runs_source_status', table_name='etl_runs')
    op.drop_table('etl_runs')
    op.drop_index(op.f('ix_etl_checkpoints_source_name'), table_name='etl_checkpoints')
    op.drop_index('idx_checkpoints_source', table_name='etl_checkpoints')
    op.drop_table('etl_checkpoints')
    op.drop_index(op.f('ix_market_data_timestamp'), table_name='market_data')
    op.drop_index(op.f('ix_market_data_coin_id'), table_name='market_data')
    op.drop_index('idx_market_data_coin_timestamp_source', table_name='market_data')
    op.drop_table('market_data')
    op.drop_index(op.f('ix_prices_timestamp'), table_name='prices')
    op.drop_index(op.f('ix_prices_coin_id'), table_name='prices')
    op.drop_index('idx_prices_coin_timestamp_source', table_name='prices')
    op.drop_table('prices')
    op.drop_index(op.f('ix_coins_source'), table_name='coins')
    op.drop_index(op.f('ix_coins_symbol'), table_name='coins')
    op.drop_index('idx_coins_symbol_source', table_name='coins')
    op.drop_table('coins')
    op.drop_index('idx_raw_csv_ingested', table_name='raw_csv')
    op.drop_table('raw_csv')
    op.drop_index('idx_raw_coingecko_ingested', table_name='raw_coingecko')
    op.drop_table('raw_coingecko')
    op.drop_index('idx_raw_coinpaprika_ingested', table_name='raw_coinpaprika')
    op.drop_table('raw_coinpaprika')

