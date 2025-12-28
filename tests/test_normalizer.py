"""Tests for data normalization."""
import pytest
from services.normalizer import Normalizer
from services.models import Coin, Price, MarketData
from datetime import datetime


def test_normalize_coinpaprika(db_session, sample_coinpaprika_data):
    """Test CoinPaprika data normalization."""
    normalizer = Normalizer(db_session)
    
    coin, price, market_data = normalizer.normalize_coinpaprika(sample_coinpaprika_data)
    
    assert coin is not None
    assert coin.symbol == "BTC"
    assert coin.name == "Bitcoin"
    assert coin.source == "coinpaprika"
    
    assert price is not None
    assert float(price.price_usd) == 45000.50
    assert float(price.market_cap_usd) == 850000000000
    assert price.source == "coinpaprika"
    
    assert market_data is not None
    assert float(market_data.price_usd) == 45000.50
    assert float(market_data.price_change_24h) == 2.5
    
    db_session.commit()
    
    # Test idempotency - should not create duplicates
    coin2, price2, market_data2 = normalizer.normalize_coinpaprika(sample_coinpaprika_data)
    assert coin2.id == coin.id
    assert price2.id == price.id
    assert market_data2.id == market_data.id


def test_normalize_coingecko(db_session, sample_coingecko_data):
    """Test CoinGecko data normalization."""
    normalizer = Normalizer(db_session)
    
    coin, price, market_data = normalizer.normalize_coingecko(sample_coingecko_data)
    
    assert coin is not None
    assert coin.symbol == "BTC"
    assert coin.name == "Bitcoin"
    assert coin.source == "coingecko"
    
    assert price is not None
    assert float(price.price_usd) == 45000.50
    assert price.source == "coingecko"
    
    db_session.commit()


def test_normalize_csv(db_session, sample_csv_data):
    """Test CSV data normalization."""
    normalizer = Normalizer(db_session)
    
    coin, price, market_data = normalizer.normalize_csv(sample_csv_data)
    
    assert coin is not None
    assert coin.symbol == "BTC"
    assert coin.name == "Bitcoin"
    assert coin.source == "csv"
    
    assert price is not None
    assert float(price.price_usd) == 45000.00
    assert price.source == "csv"
    
    db_session.commit()


def test_get_or_create_coin_idempotency(db_session):
    """Test that get_or_create_coin is idempotent."""
    normalizer = Normalizer(db_session)
    
    coin1 = normalizer.get_or_create_coin("ETH", "Ethereum", "test")
    db_session.commit()
    
    coin2 = normalizer.get_or_create_coin("ETH", "Ethereum", "test")
    db_session.commit()
    
    assert coin1.id == coin2.id
    assert coin1.symbol == coin2.symbol

