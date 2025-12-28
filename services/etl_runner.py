"""ETL runner service that orchestrates all ingesters."""
import asyncio
from sqlalchemy.orm import Session
from ingestion.coinpaprika_ingester import CoinPaprikaIngester
from ingestion.coingecko_ingester import CoinGeckoIngester
from ingestion.csv_ingester import CSVIngester
from core.config import settings
from core.logging_config import logger
from typing import List, Dict


class ETLRunner:
    """Orchestrates ETL pipeline execution."""
    
    def __init__(self, db: Session):
        """
        Initialize ETL runner.
        
        Args:
            db: Database session
        """
        self.db = db
        self.ingesters = [
            CoinPaprikaIngester(db),
            CoinGeckoIngester(db),
            CSVIngester(db, csv_path="data/sample_coins.csv"),
        ]
    
    async def run_all(self) -> Dict[str, Dict[str, int]]:
        """
        Run all ingesters.
        
        Returns:
            Dictionary mapping source names to ingestion results
        """
        results = {}
        
        for ingester in self.ingesters:
            try:
                logger.info("Starting ingestion", source=ingester.source_name)
                result = await ingester.ingest()
                results[ingester.source_name] = result
                logger.info(
                    "Ingestion completed",
                    source=ingester.source_name,
                    ingested=result.get("ingested", 0),
                    normalized=result.get("normalized", 0)
                )
            except Exception as e:
                logger.error(
                    "Ingestion failed",
                    source=ingester.source_name,
                    error=str(e)
                )
                results[ingester.source_name] = {
                    "ingested": 0,
                    "normalized": 0,
                    "error": str(e)
                }
        
        return results
    
    async def run_continuous(self):
        """
        Run ETL continuously with interval.
        
        This method runs the ETL pipeline in a loop with the configured interval.
        """
        logger.info(
            "Starting continuous ETL runner",
            interval_seconds=settings.ETL_RUN_INTERVAL_SECONDS
        )
        
        while True:
            try:
                await self.run_all()
            except Exception as e:
                logger.error("ETL run failed", error=str(e))
            
            # Wait for next run
            await asyncio.sleep(settings.ETL_RUN_INTERVAL_SECONDS)

