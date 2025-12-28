"""Tests for ETL failure recovery."""
import pytest
from services.models import ETLRun, ETLStatus
from datetime import datetime


def test_etl_run_tracking(db_session):
    """Test that ETL runs are tracked."""
    # Create a failed run
    failed_run = ETLRun(
        source_name="test_source",
        status=ETLStatus.FAILED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error_message="Test error"
    )
    db_session.add(failed_run)
    
    # Create a successful run
    success_run = ETLRun(
        source_name="test_source",
        status=ETLStatus.SUCCESS,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        records_ingested=10,
        records_normalized=10
    )
    db_session.add(success_run)
    db_session.commit()
    
    # Query runs
    runs = db_session.query(ETLRun).filter(
        ETLRun.source_name == "test_source"
    ).all()
    
    assert len(runs) == 2
    assert any(r.status == ETLStatus.FAILED for r in runs)
    assert any(r.status == ETLStatus.SUCCESS for r in runs)


def test_etl_run_error_message(db_session):
    """Test that error messages are stored."""
    error_message = "Connection timeout"
    failed_run = ETLRun(
        source_name="test_source",
        status=ETLStatus.FAILED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error_message=error_message
    )
    db_session.add(failed_run)
    db_session.commit()
    
    run = db_session.query(ETLRun).filter(
        ETLRun.source_name == "test_source"
    ).first()
    
    assert run.error_message == error_message


def test_etl_run_metadata(db_session):
    """Test that ETL run metadata is stored."""
    run = ETLRun(
        source_name="test_source",
        status=ETLStatus.SUCCESS,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        records_ingested=100,
        records_normalized=95
    )
    db_session.add(run)
    db_session.commit()
    
    assert run.records_ingested == 100
    assert run.records_normalized == 95
    assert run.completed_at is not None

