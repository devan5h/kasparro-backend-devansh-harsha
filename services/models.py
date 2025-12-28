"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database import Base


class ETLStatus(str, enum.Enum):
    """ETL run status enumeration."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# Raw Data Tables
class RawCoinPaprika(Base):
    """Raw data from CoinPaprika API."""
    __tablename__ = "raw_coinpaprika"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data = Column(Text, nullable=False)  # JSON as text
    ingested_at = Column(DateTime, default=func.now(), nullable=False)
    source_id = Column(String, nullable=True)  # CoinPaprika coin ID
    
    # Index for efficient querying
    __table_args__ = (
        Index('idx_raw_coinpaprika_ingested', 'ingested_at'),
    )


class RawCoinGecko(Base):
    """Raw data from CoinGecko API."""
    __tablename__ = "raw_coingecko"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data = Column(Text, nullable=False)  # JSON as text
    ingested_at = Column(DateTime, default=func.now(), nullable=False)
    source_id = Column(String, nullable=True)  # CoinGecko coin ID
    
    __table_args__ = (
        Index('idx_raw_coingecko_ingested', 'ingested_at'),
    )


class RawCSV(Base):
    """Raw data from CSV files."""
    __tablename__ = "raw_csv"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data = Column(Text, nullable=False)  # CSV row as JSON
    ingested_at = Column(DateTime, default=func.now(), nullable=False)
    source_id = Column(String, nullable=True)  # Row identifier
    
    __table_args__ = (
        Index('idx_raw_csv_ingested', 'ingested_at'),
    )


# Normalized Tables
class Coin(Base):
    """Normalized coin table."""
    __tablename__ = "coins"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    source = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    prices = relationship("Price", back_populates="coin")
    market_data = relationship("MarketData", back_populates="coin")
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        Index('idx_coins_symbol_source', 'symbol', 'source', unique=True),
    )


class Price(Base):
    """Normalized price table."""
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False, index=True)
    price_usd = Column(Numeric(20, 8), nullable=False)
    market_cap_usd = Column(Numeric(20, 2), nullable=True)
    volume_24h_usd = Column(Numeric(20, 2), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    coin = relationship("Coin", back_populates="prices")
    
    # Unique constraint to prevent duplicate prices for same coin/timestamp/source
    __table_args__ = (
        Index('idx_prices_coin_timestamp_source', 'coin_id', 'timestamp', 'source', unique=True),
    )


class MarketData(Base):
    """Normalized market data table (alternative view of price data)."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False, index=True)
    price_usd = Column(Numeric(20, 8), nullable=False)
    market_cap_usd = Column(Numeric(20, 2), nullable=True)
    volume_24h_usd = Column(Numeric(20, 2), nullable=True)
    price_change_24h = Column(Numeric(10, 4), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    coin = relationship("Coin", back_populates="market_data")
    
    __table_args__ = (
        Index('idx_market_data_coin_timestamp_source', 'coin_id', 'timestamp', 'source', unique=True),
    )


# Checkpoint Table for Incremental Ingestion
class ETLCheckpoint(Base):
    """Checkpoint table for tracking ETL progress and enabling incremental ingestion."""
    __tablename__ = "etl_checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), nullable=False, index=True, unique=True)  # coinpaprika, coingecko, csv
    last_ingested_id = Column(String(200), nullable=True)  # Last processed ID from source
    last_ingested_timestamp = Column(DateTime, nullable=True)  # Last processed timestamp (renamed for clarity)
    last_successful_timestamp = Column(DateTime, nullable=True)  # Last successfully processed timestamp (only updated on success)
    last_run_id = Column(Integer, ForeignKey("etl_runs.id"), nullable=True)  # Last successful ETL run ID
    checkpoint_data = Column(Text, nullable=True)  # JSON for additional checkpoint info
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_checkpoints_source', 'source_name', unique=True),
    )


# ETL Run Metadata Table
class ETLRun(Base):
    """ETL run metadata for tracking execution history."""
    __tablename__ = "etl_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), nullable=False, index=True)
    status = Column(SQLEnum(ETLStatus), nullable=False, index=True)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    records_ingested = Column(Integer, default=0)
    records_normalized = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    run_metadata = Column(Text, nullable=True)  # JSON for additional run info
    
    __table_args__ = (
        Index('idx_etl_runs_source_status', 'source_name', 'status'),
        Index('idx_etl_runs_started', 'started_at'),
    )

