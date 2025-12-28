"""CoinGecko API ingester."""
import json
from sqlalchemy.orm import Session
from services.models import RawCoinGecko
from services.http_client import HTTPClient, get_with_retry
from services.rate_limiter import RateLimiter
from services.normalizer import Normalizer
from ingestion.base_ingester import BaseIngester
from core.config import settings
from core.logging_config import logger
from typing import Dict, List, Any, Optional
from datetime import datetime


class CoinGeckoIngester(BaseIngester):
    """Ingester for CoinGecko API."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, db: Session):
        """
        Initialize CoinGecko ingester.
        
        Args:
            db: Database session
        """
        super().__init__(db, "coingecko")
        self.rate_limiter = RateLimiter(rate=settings.COINGECKO_RATE_LIMIT)
        self.normalizer = Normalizer(db)
    
    async def _fetch_coins_markets(self, http_client: HTTPClient, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch coin market data from CoinGecko.
        
        Args:
            http_client: HTTP client instance
            page: Page number
            per_page: Items per page
            
        Returns:
            List of market data
        """
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false"
        }
        response = await get_with_retry(
            http_client=http_client,
            url=url,
            source=self.source_name,
            params=params
        )
        return response.json()
    
    def save_raw_data(self, raw_data: Dict[str, Any], source_id: Optional[str] = None):
        """
        Save raw data to raw_coingecko table.
        
        Args:
            raw_data: Raw data dictionary
            source_id: Coin ID from CoinGecko
        """
        raw_record = RawCoinGecko(
            raw_data=json.dumps(raw_data),
            source_id=source_id
        )
        self.db.add(raw_record)
    
    def _safe_datetime(self, value: Any) -> Optional[datetime]:
        """Safely convert value to datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
    
    async def ingest(self) -> Dict[str, int]:
        """
        Perform CoinGecko ingestion with timestamp-based incremental processing.
        Only processes records newer than last_successful_timestamp.
        
        Returns:
            Dictionary with 'ingested' and 'normalized' counts
        """
        self.start_run()
        ingested_count = 0
        normalized_count = 0
        latest_timestamp: Optional[datetime] = None
        
        try:
            async with HTTPClient(rate_limiter=self.rate_limiter) as http_client:
                # Get checkpoint to determine incremental start point
                checkpoint = self.checkpoint_manager.get_checkpoint(self.source_name)
                last_successful_timestamp = checkpoint.last_successful_timestamp if checkpoint else None
                
                if last_successful_timestamp:
                    logger.info(
                        "Starting incremental ingestion",
                        source=self.source_name,
                        last_timestamp=last_successful_timestamp.isoformat()
                    )
                else:
                    logger.info("Starting full ingestion (no checkpoint)", source=self.source_name)
                
                # Fetch market data (limit to first 3 pages for demo)
                max_pages = 3
                for page in range(1, max_pages + 1):
                    markets = await self._fetch_coins_markets(http_client, page=page)
                    
                    if not markets:
                        break
                    
                    logger.info("Fetched market data from CoinGecko", page=page, count=len(markets))
                    
                    for market in markets:
                        coin_id = market.get("id")
                        
                        # Extract timestamp from market data
                        record_timestamp = self._safe_datetime(market.get("last_updated"))
                        
                        # INCREMENTAL FILTER: Only process if newer than last successful timestamp
                        if last_successful_timestamp and record_timestamp:
                            # Normalize timezones for comparison (make both timezone-aware or both naive)
                            if record_timestamp.tzinfo is None and last_successful_timestamp.tzinfo is not None:
                                # Record is naive, checkpoint is aware - make record aware (assume UTC)
                                from datetime import timezone
                                record_timestamp = record_timestamp.replace(tzinfo=timezone.utc)
                            elif record_timestamp.tzinfo is not None and last_successful_timestamp.tzinfo is None:
                                # Record is aware, checkpoint is naive - make checkpoint aware (assume UTC)
                                from datetime import timezone
                                last_successful_timestamp = last_successful_timestamp.replace(tzinfo=timezone.utc)
                            
                            if record_timestamp <= last_successful_timestamp:
                                continue  # Skip already processed records
                        
                        self.save_raw_data(market, source_id=coin_id)
                        ingested_count += 1
                        
                        # Normalize and save (UPSERT handles idempotency)
                        coin, price, market_data = self.normalizer.normalize_coingecko(market)
                        if coin and price:
                            normalized_count += 1
                            # Track latest timestamp processed
                            if record_timestamp and (latest_timestamp is None or record_timestamp > latest_timestamp):
                                latest_timestamp = record_timestamp
                            self.db.commit()
                
                # Update checkpoint ONLY on success with latest timestamp
                if latest_timestamp:
                    self.complete_run(ingested_count, normalized_count, last_successful_timestamp=latest_timestamp)
                else:
                    # No new records processed, but run was successful
                    self.complete_run(ingested_count, normalized_count, last_successful_timestamp=last_successful_timestamp)
                
                return {"ingested": ingested_count, "normalized": normalized_count}
        
        except Exception as e:
            error_msg = f"CoinGecko ingestion failed: {str(e)}"
            self.fail_run(error_msg)
            # Checkpoint NOT updated on failure - preserves last_successful_timestamp
            raise

