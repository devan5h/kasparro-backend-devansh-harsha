"""Data normalization service for converting raw data to unified schema."""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert
from services.models import Coin, Price, MarketData
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, Tuple
from core.logging_config import logger
import json


class Normalizer:
    """Normalizes raw data from different sources into unified schema."""
    
    def __init__(self, db: Session):
        """
        Initialize normalizer.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _safe_decimal(self, value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Safely convert value to Decimal.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Decimal or None
        """
        if value is None:
            return default
        
        try:
            if isinstance(value, str):
                # Remove commas and other formatting
                value = value.replace(",", "").strip()
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return default
    
    def _safe_datetime(self, value: Any) -> datetime:
        """
        Safely convert value to datetime.
        
        Args:
            value: Value to convert
            
        Returns:
            Datetime or current time if conversion fails
        """
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, (int, float)):
            # Unix timestamp
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return datetime.utcnow()
        
        # Try parsing string
        if isinstance(value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        return datetime.utcnow()
    
    def get_or_create_coin(self, symbol: str, name: str, source: str) -> Coin:
        """
        Get or create a coin record (idempotent).
        
        Args:
            symbol: Coin symbol
            name: Coin name
            source: Data source
            
        Returns:
            Coin instance
        """
        # Normalize symbol to uppercase
        symbol = symbol.upper().strip()
        
        # Check if coin exists
        coin = self.db.query(Coin).filter(
            and_(Coin.symbol == symbol, Coin.source == source)
        ).first()
        
        if not coin:
            coin = Coin(
                symbol=symbol,
                name=name.strip(),
                source=source
            )
            self.db.add(coin)
            self.db.flush()  # Flush to get ID
            logger.debug("Created new coin", symbol=symbol, source=source)
        else:
            # Update name if changed
            if coin.name != name.strip():
                coin.name = name.strip()
                coin.updated_at = datetime.utcnow()
        
        return coin
    
    def normalize_coinpaprika(self, raw_data: Dict[str, Any]) -> Tuple[Optional[Coin], Optional[Price], Optional[MarketData]]:
        """
        Normalize CoinPaprika data.
        
        Args:
            raw_data: Raw data from CoinPaprika API
            
        Returns:
            Tuple of (Coin, Price, MarketData) or None values
        """
        try:
            symbol = raw_data.get("symbol", "").upper()
            name = raw_data.get("name", "")
            
            if not symbol or not name:
                return None, None, None
            
            # Get or create coin
            coin = self.get_or_create_coin(symbol, name, "coinpaprika")
            
            # Extract price data
            quotes = raw_data.get("quotes", {})
            usd_data = quotes.get("USD", {})
            
            price_usd = self._safe_decimal(usd_data.get("price"))
            market_cap = self._safe_decimal(usd_data.get("market_cap"))
            volume_24h = self._safe_decimal(usd_data.get("volume_24h"))
            price_change_24h = self._safe_decimal(usd_data.get("percent_change_24h"))
            
            timestamp = self._safe_datetime(raw_data.get("last_updated"))
            
            if price_usd is None:
                return coin, None, None
            
            # Create price record (idempotent)
            price = self._get_or_create_price(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=volume_24h,
                timestamp=timestamp,
                source="coinpaprika"
            )
            
            # Create market data record (idempotent)
            market_data = self._get_or_create_market_data(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=volume_24h,
                price_change_24h=price_change_24h,
                timestamp=timestamp,
                source="coinpaprika"
            )
            
            return coin, price, market_data
        
        except Exception as e:
            logger.error("Failed to normalize CoinPaprika data", error=str(e))
            return None, None, None
    
    def normalize_coingecko(self, raw_data: Dict[str, Any]) -> Tuple[Optional[Coin], Optional[Price], Optional[MarketData]]:
        """
        Normalize CoinGecko data.
        
        Args:
            raw_data: Raw data from CoinGecko API
            
        Returns:
            Tuple of (Coin, Price, MarketData) or None values
        """
        try:
            symbol = raw_data.get("symbol", "").upper()
            name = raw_data.get("name", "")
            
            if not symbol or not name:
                return None, None, None
            
            # Get or create coin
            coin = self.get_or_create_coin(symbol, name, "coingecko")
            
            # Extract price data
            price_usd = self._safe_decimal(raw_data.get("current_price"))
            market_cap = self._safe_decimal(raw_data.get("market_cap"))
            volume_24h = self._safe_decimal(raw_data.get("total_volume"))
            price_change_24h = self._safe_decimal(raw_data.get("price_change_percentage_24h"))
            
            # CoinGecko uses last_updated field
            timestamp = self._safe_datetime(raw_data.get("last_updated"))
            
            if price_usd is None:
                return coin, None, None
            
            # Create price record
            price = self._get_or_create_price(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=volume_24h,
                timestamp=timestamp,
                source="coingecko"
            )
            
            # Create market data record
            market_data = self._get_or_create_market_data(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=volume_24h,
                price_change_24h=price_change_24h,
                timestamp=timestamp,
                source="coingecko"
            )
            
            return coin, price, market_data
        
        except Exception as e:
            logger.error("Failed to normalize CoinGecko data", error=str(e))
            return None, None, None
    
    def normalize_csv(self, raw_data: Dict[str, Any]) -> Tuple[Optional[Coin], Optional[Price], Optional[MarketData]]:
        """
        Normalize CSV data.
        
        Args:
            raw_data: Raw data from CSV file
            
        Returns:
            Tuple of (Coin, Price, MarketData) or None values
        """
        try:
            symbol = raw_data.get("symbol", "").upper()
            name = raw_data.get("name", "")
            
            if not symbol or not name:
                return None, None, None
            
            # Get or create coin
            coin = self.get_or_create_coin(symbol, name, "csv")
            
            # Extract price data
            price_usd = self._safe_decimal(raw_data.get("price_usd"))
            market_cap = self._safe_decimal(raw_data.get("market_cap"))
            
            # Use current time for CSV data
            timestamp = datetime.utcnow()
            
            if price_usd is None:
                return coin, None, None
            
            # Create price record
            price = self._get_or_create_price(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=None,
                timestamp=timestamp,
                source="csv"
            )
            
            # Create market data record
            market_data = self._get_or_create_market_data(
                coin_id=coin.id,
                price_usd=price_usd,
                market_cap_usd=market_cap,
                volume_24h_usd=None,
                price_change_24h=None,
                timestamp=timestamp,
                source="csv"
            )
            
            return coin, price, market_data
        
        except Exception as e:
            logger.error("Failed to normalize CSV data", error=str(e))
            return None, None, None
    
    def _get_or_create_price(
        self,
        coin_id: int,
        price_usd: Decimal,
        market_cap_usd: Optional[Decimal],
        volume_24h_usd: Optional[Decimal],
        timestamp: datetime,
        source: str
    ) -> Optional[Price]:
        """
        Get or create price record (idempotent using UPSERT).
        Uses PostgreSQL ON CONFLICT DO NOTHING to prevent duplicates.
        
        Args:
            coin_id: Coin ID
            price_usd: Price in USD
            market_cap_usd: Market cap in USD
            volume_24h_usd: 24h volume in USD
            timestamp: Price timestamp
            source: Data source
            
        Returns:
            Price instance or None
        """
        # Use UPSERT with ON CONFLICT DO NOTHING for idempotency
        # This leverages the UNIQUE constraint on (coin_id, timestamp, source)
        stmt = insert(Price).values(
            coin_id=coin_id,
            price_usd=price_usd,
            market_cap_usd=market_cap_usd,
            volume_24h_usd=volume_24h_usd,
            timestamp=timestamp,
            source=source
        ).on_conflict_do_nothing(
            index_elements=['coin_id', 'timestamp', 'source']
        ).returning(Price)
        
        result = self.db.execute(stmt)
        self.db.flush()
        
        # If insert succeeded, get the new record; otherwise query existing
        inserted = result.first()
        if inserted:
            return inserted[0]
        
        # If conflict occurred, fetch existing record
        existing = self.db.query(Price).filter(
            and_(
                Price.coin_id == coin_id,
                Price.timestamp == timestamp,
                Price.source == source
            )
        ).first()
        return existing
    
    def _get_or_create_market_data(
        self,
        coin_id: int,
        price_usd: Decimal,
        market_cap_usd: Optional[Decimal],
        volume_24h_usd: Optional[Decimal],
        price_change_24h: Optional[Decimal],
        timestamp: datetime,
        source: str
    ) -> Optional[MarketData]:
        """
        Get or create market data record (idempotent using UPSERT).
        Uses PostgreSQL ON CONFLICT DO NOTHING to prevent duplicates.
        
        Args:
            coin_id: Coin ID
            price_usd: Price in USD
            market_cap_usd: Market cap in USD
            volume_24h_usd: 24h volume in USD
            price_change_24h: 24h price change percentage
            timestamp: Data timestamp
            source: Data source
            
        Returns:
            MarketData instance or None
        """
        # Use UPSERT with ON CONFLICT DO NOTHING for idempotency
        # This leverages the UNIQUE constraint on (coin_id, timestamp, source)
        stmt = insert(MarketData).values(
            coin_id=coin_id,
            price_usd=price_usd,
            market_cap_usd=market_cap_usd,
            volume_24h_usd=volume_24h_usd,
            price_change_24h=price_change_24h,
            timestamp=timestamp,
            source=source
        ).on_conflict_do_nothing(
            index_elements=['coin_id', 'timestamp', 'source']
        ).returning(MarketData)
        
        result = self.db.execute(stmt)
        self.db.flush()
        
        # If insert succeeded, get the new record; otherwise query existing
        inserted = result.first()
        if inserted:
            return inserted[0]
        
        # If conflict occurred, fetch existing record
        existing = self.db.query(MarketData).filter(
            and_(
                MarketData.coin_id == coin_id,
                MarketData.timestamp == timestamp,
                MarketData.source == source
            )
        ).first()
        return existing

