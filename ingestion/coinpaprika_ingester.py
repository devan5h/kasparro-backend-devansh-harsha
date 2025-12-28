"""CoinPaprika API ingester."""
import json
from sqlalchemy.orm import Session
from services.models import RawCoinPaprika
from services.http_client import HTTPClient, get_with_retry
from services.rate_limiter import RateLimiter
from services.normalizer import Normalizer
from ingestion.base_ingester import BaseIngester
from core.config import settings
from core.logging_config import logger
from typing import Dict, List, Any, Optional
from datetime import datetime


class CoinPaprikaIngester(BaseIngester):
    """Ingester for CoinPaprika API."""
    
    BASE_URL = "https://api.coinpaprika.com/v1"
    
    def __init__(self, db: Session):
        """
        Initialize CoinPaprika ingester.
        
        Args:
            db: Database session
        """
        super().__init__(db, "coinpaprika")
        self.rate_limiter = RateLimiter(rate=settings.COINPAPRIKA_RATE_LIMIT)
        self.api_key = settings.COINPAPRIKA_API_KEY
        self.normalizer = Normalizer(db)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with API key if available."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers
    
    async def _fetch_coins(self, http_client: HTTPClient) -> List[Dict[str, Any]]:
        """
        Fetch list of coins from CoinPaprika.
        
        Args:
            http_client: HTTP client instance
            
        Returns:
            List of coin data
        """
        url = f"{self.BASE_URL}/coins"
        response = await get_with_retry(
            http_client=http_client,
            url=url,
            source=self.source_name,
            headers=self._get_headers()
        )
        return response.json()
    
    async def _fetch_coin_ticker(self, http_client: HTTPClient, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data for a specific coin.
        
        Args:
            http_client: HTTP client instance
            coin_id: Coin identifier
            
        Returns:
            Ticker data or None
        """
        url = f"{self.BASE_URL}/tickers/{coin_id}"
        try:
            response = await get_with_retry(
                http_client=http_client,
                url=url,
                source=self.source_name,
                headers=self._get_headers()
            )
            return response.json()
        except Exception as e:
            logger.warning("Failed to fetch ticker", coin_id=coin_id, error=str(e))
            return None
    
    def save_raw_data(self, raw_data: Dict[str, Any], source_id: Optional[str] = None):
        """
        Save raw data to raw_coinpaprika table.
        
        Args:
            raw_data: Raw data dictionary
            source_id: Coin ID from CoinPaprika
        """
        raw_record = RawCoinPaprika(
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
        Perform CoinPaprika ingestion with timestamp-based incremental processing.
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
                
                # Fetch list of coins
                coins = await self._fetch_coins(http_client)
                logger.info("Fetched coins from CoinPaprika", count=len(coins))
                
                # Process coins (limit to top 100 for demo, can be adjusted)
                coins_to_process = coins[:100]
                
                # Process coins incrementally
                for coin in coins_to_process:
                    coin_id = coin.get("id")
                    
                    # Fetch detailed ticker data
                    ticker_data = await self._fetch_coin_ticker(http_client, coin_id)
                    
                    if ticker_data:
                        # Extract timestamp from ticker data
                        record_timestamp = self._safe_datetime(ticker_data.get("last_updated"))
                        
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
                        
                        # Save raw data
                        self.save_raw_data(ticker_data, source_id=coin_id)
                        ingested_count += 1
                        
                        # Normalize and save (UPSERT handles idempotency)
                        coin_obj, price, market_data = self.normalizer.normalize_coinpaprika(ticker_data)
                        if coin_obj and price:
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
            error_msg = f"CoinPaprika ingestion failed: {str(e)}"
            self.fail_run(error_msg)
            # Checkpoint NOT updated on failure - preserves last_successful_timestamp
            raise

