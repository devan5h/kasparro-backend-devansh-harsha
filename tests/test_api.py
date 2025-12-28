"""Tests for API endpoints."""
import pytest
from services.models import Coin, MarketData, ETLRun, ETLStatus
from datetime import datetime
from decimal import Decimal


@pytest.fixture
def sample_market_data(db_session):
    """Create sample market data for testing."""
    coin = Coin(
        symbol="BTC",
        name="Bitcoin",
        source="test"
    )
    db_session.add(coin)
    db_session.flush()
    
    market_data = MarketData(
        coin_id=coin.id,
        price_usd=Decimal("45000.50"),
        market_cap_usd=Decimal("850000000000"),
        volume_24h_usd=Decimal("25000000000"),
        price_change_24h=Decimal("2.5"),
        timestamp=datetime.utcnow(),
        source="test"
    )
    db_session.add(market_data)
    db_session.commit()
    
    return market_data


def test_get_data_endpoint(client, sample_market_data):
    """Test GET /api/data endpoint."""
    response = client.get("/api/data")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "pagination" in data
    assert "metadata" in data
    assert "request_id" in data["metadata"]
    assert "api_latency_ms" in data["metadata"]
    assert len(data["data"]) > 0


def test_get_data_pagination(client, db_session):
    """Test pagination in GET /api/data."""
    # Create multiple market data entries
    coin = Coin(symbol="ETH", name="Ethereum", source="test")
    db_session.add(coin)
    db_session.flush()
    
    for i in range(5):
        market_data = MarketData(
            coin_id=coin.id,
            price_usd=Decimal("2800.00"),
            timestamp=datetime.utcnow(),
            source="test"
        )
        db_session.add(market_data)
    db_session.commit()
    
    # Test first page
    response = client.get("/api/data?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["has_next"] is True


def test_get_data_filtering(client, sample_market_data):
    """Test filtering in GET /api/data."""
    # Filter by symbol
    response = client.get("/api/data?symbol=BTC")
    assert response.status_code == 200
    data = response.json()
    assert all(item["coin"]["symbol"] == "BTC" for item in data["data"])
    
    # Filter by source
    response = client.get("/api/data?source=test")
    assert response.status_code == 200
    data = response.json()
    assert all(item["source"] == "test" for item in data["data"])


def test_health_endpoint(client, db_session):
    """Test GET /api/health endpoint."""
    # Create a test ETL run
    etl_run = ETLRun(
        source_name="test_source",
        status=ETLStatus.SUCCESS,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        records_ingested=10,
        records_normalized=10
    )
    db_session.add(etl_run)
    db_session.commit()
    
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "database" in data
    assert "etl_last_run" in data
    assert data["database"] == "healthy"


def test_stats_endpoint(client, db_session):
    """Test GET /api/stats endpoint."""
    # Create multiple ETL runs
    for i in range(3):
        etl_run = ETLRun(
            source_name="test_source",
            status=ETLStatus.SUCCESS if i < 2 else ETLStatus.FAILED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            records_ingested=10,
            records_normalized=10
        )
        db_session.add(etl_run)
    db_session.commit()
    
    response = client.get("/api/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_runs" in data
    assert "successful_runs" in data
    assert "failed_runs" in data
    assert "runs" in data
    assert data["total_runs"] == 3
    assert data["successful_runs"] == 2
    assert data["failed_runs"] == 1


def test_stats_filter_by_source(client, db_session):
    """Test stats endpoint with source filter."""
    # Create runs for different sources
    for source in ["source1", "source2"]:
        etl_run = ETLRun(
            source_name=source,
            status=ETLStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db_session.add(etl_run)
    db_session.commit()
    
    response = client.get("/api/stats?source=source1")
    assert response.status_code == 200
    data = response.json()
    assert data["total_runs"] == 1

