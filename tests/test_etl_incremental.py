"""Tests for incremental ETL ingestion."""
import pytest
from services.checkpoint_manager import CheckpointManager
from services.models import ETLCheckpoint, RawCoinPaprika
from datetime import datetime
import json


def test_incremental_ingestion_resume(db_session):
    """Test that ETL can resume from checkpoint."""
    manager = CheckpointManager(db_session)
    
    # Set checkpoint
    manager.update_checkpoint(
        "coinpaprika",
        last_ingested_id="btc-bitcoin"
    )
    
    checkpoint = manager.get_checkpoint("coinpaprika")
    assert checkpoint.last_ingested_id == "btc-bitcoin"


def test_checkpoint_after_failure(db_session):
    """Test checkpoint is saved even after partial ingestion."""
    manager = CheckpointManager(db_session)
    
    # Simulate partial ingestion
    raw_data = RawCoinPaprika(
        raw_data=json.dumps({"id": "eth-ethereum", "symbol": "ETH"}),
        source_id="eth-ethereum"
    )
    db_session.add(raw_data)
    db_session.commit()
    
    # Update checkpoint
    manager.update_checkpoint(
        "coinpaprika",
        last_ingested_id="eth-ethereum"
    )
    
    checkpoint = manager.get_checkpoint("coinpaprika")
    assert checkpoint.last_ingested_id == "eth-ethereum"


def test_idempotent_writes(db_session):
    """Test that duplicate writes are prevented."""
    from services.normalizer import Normalizer
    
    normalizer = Normalizer(db_session)
    
    # Create same coin twice
    coin1 = normalizer.get_or_create_coin("BTC", "Bitcoin", "test")
    db_session.commit()
    
    coin2 = normalizer.get_or_create_coin("BTC", "Bitcoin", "test")
    db_session.commit()
    
    # Should be the same coin
    assert coin1.id == coin2.id
    
    # Count coins
    from services.models import Coin
    count = db_session.query(Coin).filter(Coin.symbol == "BTC").count()
    assert count == 1

