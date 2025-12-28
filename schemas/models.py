"""Pydantic models for data validation and serialization."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Coin Schema
class CoinBase(BaseModel):
    """Base coin schema."""
    symbol: str = Field(..., description="Coin symbol (e.g., BTC)")
    name: str = Field(..., description="Coin name")
    source: str = Field(..., description="Data source (coinpaprika, coingecko, csv)")


class CoinCreate(CoinBase):
    """Schema for creating a coin."""
    pass


class Coin(CoinBase):
    """Coin schema with ID."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Price Schema
class PriceBase(BaseModel):
    """Base price schema."""
    coin_id: int
    price_usd: Decimal = Field(..., description="Price in USD")
    market_cap_usd: Optional[Decimal] = Field(None, description="Market cap in USD")
    volume_24h_usd: Optional[Decimal] = Field(None, description="24h volume in USD")
    timestamp: datetime = Field(..., description="Price timestamp")
    source: str = Field(..., description="Data source")


class PriceCreate(PriceBase):
    """Schema for creating a price."""
    pass


class Price(PriceBase):
    """Price schema with ID."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Market Data Schema
class MarketDataBase(BaseModel):
    """Base market data schema."""
    coin_id: int
    price_usd: Decimal
    market_cap_usd: Optional[Decimal] = None
    volume_24h_usd: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    timestamp: datetime
    source: str


class MarketDataCreate(MarketDataBase):
    """Schema for creating market data."""
    pass


class MarketData(MarketDataBase):
    """Market data schema with ID."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Metadata(BaseModel):
    request_id: str
    api_latency_ms: int


# API Response Schemas
class DataResponse(BaseModel):
    """Response schema for /data endpoint."""
    metadata: Metadata
    data: List[dict]
    pagination: dict


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    status: str
    database: str
    etl_last_run: Optional[dict] = None


class StatsResponse(BaseModel):
    """Response schema for /stats endpoint."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_run: Optional[dict] = None
    runs: List[dict]

