"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.database import Base, get_db
from services.models import (
    RawCoinPaprika,
    RawCoinGecko,
    RawCSV,
    Coin,
    Price,
    MarketData,
    ETLCheckpoint,
    ETLRun,
)
from fastapi.testclient import TestClient
from api.main import app
import os


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_coinpaprika_data():
    """Sample CoinPaprika API response."""
    return {
        "id": "btc-bitcoin",
        "name": "Bitcoin",
        "symbol": "BTC",
        "quotes": {
            "USD": {
                "price": 45000.50,
                "market_cap": 850000000000,
                "volume_24h": 25000000000,
                "percent_change_24h": 2.5
            }
        },
        "last_updated": 1234567890
    }


@pytest.fixture
def sample_coingecko_data():
    """Sample CoinGecko API response."""
    return {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 45000.50,
        "market_cap": 850000000000,
        "total_volume": 25000000000,
        "price_change_percentage_24h": 2.5,
        "last_updated": "2023-01-01T00:00:00.000Z"
    }


@pytest.fixture
def sample_csv_data():
    """Sample CSV row data."""
    return {
        "symbol": "BTC",
        "name": "Bitcoin",
        "price_usd": "45000.00",
        "market_cap": "850000000000"
    }

