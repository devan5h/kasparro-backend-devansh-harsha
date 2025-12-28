"""Tests for checkpoint management."""
import pytest
from services.checkpoint_manager import CheckpointManager
from services.models import ETLCheckpoint
from datetime import datetime


def test_create_checkpoint(db_session):
    """Test creating a checkpoint."""
    manager = CheckpointManager(db_session)
    
    manager.update_checkpoint(
        "test_source",
        last_ingested_id="test_id_123",
        last_ingested_timestamp=datetime.utcnow()
    )
    
    checkpoint = manager.get_checkpoint("test_source")
    assert checkpoint is not None
    assert checkpoint.source_name == "test_source"
    assert checkpoint.last_ingested_id == "test_id_123"


def test_update_checkpoint(db_session):
    """Test updating an existing checkpoint."""
    manager = CheckpointManager(db_session)
    
    # Create initial checkpoint
    manager.update_checkpoint("test_source", last_ingested_id="id_1")
    
    # Update checkpoint
    manager.update_checkpoint("test_source", last_ingested_id="id_2")
    
    checkpoint = manager.get_checkpoint("test_source")
    assert checkpoint.last_ingested_id == "id_2"


def test_checkpoint_data_json(db_session):
    """Test checkpoint data with JSON."""
    manager = CheckpointManager(db_session)
    
    checkpoint_data = {"last_page": 5, "last_timestamp": "2023-01-01"}
    manager.update_checkpoint(
        "test_source",
        checkpoint_data=checkpoint_data
    )
    
    data = manager.get_checkpoint_data("test_source")
    assert data is not None
    assert data["last_page"] == 5

