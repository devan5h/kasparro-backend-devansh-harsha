"""CSV file ingester."""
import json
import csv
import os
from sqlalchemy.orm import Session
from services.models import RawCSV
from services.normalizer import Normalizer
from ingestion.base_ingester import BaseIngester
from core.logging_config import logger
from typing import Dict, Optional, List, Any
from pathlib import Path
from datetime import datetime


class CSVIngester(BaseIngester):
    """Ingester for CSV files."""
    
    def __init__(self, db: Session, csv_path: str = "data/sample_coins.csv"):
        """
        Initialize CSV ingester.
        
        Args:
            db: Database session
            csv_path: Path to CSV file
        """
        super().__init__(db, "csv")
        self.csv_path = csv_path
        self.normalizer = Normalizer(db)
    
    def save_raw_data(self, raw_data: Dict[str, Any], source_id: Optional[str] = None):
        """
        Save raw data to raw_csv table.
        
        Args:
            raw_data: Raw data dictionary
            source_id: Row identifier
        """
        raw_record = RawCSV(
            raw_data=json.dumps(raw_data),
            source_id=source_id
        )
        self.db.add(raw_record)
    
    async def ingest(self) -> Dict[str, int]:
        """
        Perform CSV ingestion with timestamp-based incremental processing.
        CSV records use current timestamp; only processes if file modified since last run.
        
        Returns:
            Dictionary with 'ingested' and 'normalized' counts
        """
        self.start_run()
        ingested_count = 0
        normalized_count = 0
        latest_timestamp: Optional[datetime] = None
        
        try:
            # Check if CSV file exists
            if not os.path.exists(self.csv_path):
                logger.warning("CSV file not found, creating sample", path=self.csv_path)
                # Create sample CSV if it doesn't exist
                os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
                self._create_sample_csv()
            
            # Get checkpoint to determine incremental start point
            checkpoint = self.checkpoint_manager.get_checkpoint(self.source_name)
            last_successful_timestamp = checkpoint.last_successful_timestamp if checkpoint else None
            
            # For CSV, check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self.csv_path))
            
            # INCREMENTAL FILTER: Only process if file modified since last successful run
            if last_successful_timestamp and file_mtime <= last_successful_timestamp:
                logger.info(
                    "CSV file not modified since last run",
                    source=self.source_name,
                    file_mtime=file_mtime.isoformat(),
                    last_timestamp=last_successful_timestamp.isoformat()
                )
                self.complete_run(0, 0, last_successful_timestamp=last_successful_timestamp)
                return {"ingested": 0, "normalized": 0}
            
            if last_successful_timestamp:
                logger.info(
                    "Starting incremental ingestion",
                    source=self.source_name,
                    last_timestamp=last_successful_timestamp.isoformat(),
                    file_mtime=file_mtime.isoformat()
                )
            else:
                logger.info("Starting full ingestion (no checkpoint)", source=self.source_name)
            
            # Read and process CSV
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Process all rows (CSV uses current timestamp, so all are "new")
            # UPSERT handles idempotency if same data is processed multiple times
            processing_timestamp = datetime.utcnow()
            
            for idx, row in enumerate(rows):
                row_id = f"{idx}_{row.get('symbol', '')}"
                self.save_raw_data(row, source_id=row_id)
                ingested_count += 1
                
                # Normalize and save (UPSERT handles idempotency)
                coin, price, market_data = self.normalizer.normalize_csv(row)
                if coin and price:
                    normalized_count += 1
                    # Track latest timestamp (use processing time for CSV)
                    if latest_timestamp is None or processing_timestamp > latest_timestamp:
                        latest_timestamp = processing_timestamp
                    self.db.commit()
            
            # Update checkpoint ONLY on success with latest timestamp
            if latest_timestamp:
                self.complete_run(ingested_count, normalized_count, last_successful_timestamp=latest_timestamp)
            else:
                # No records processed, but run was successful
                self.complete_run(ingested_count, normalized_count, last_successful_timestamp=last_successful_timestamp)
            
            return {"ingested": ingested_count, "normalized": normalized_count}
        
        except Exception as e:
            error_msg = f"CSV ingestion failed: {str(e)}"
            self.fail_run(error_msg)
            # Checkpoint NOT updated on failure - preserves last_successful_timestamp
            raise
    
    def _create_sample_csv(self):
        """Create a sample CSV file for testing."""
        sample_data = [
            {"symbol": "BTC", "name": "Bitcoin", "price_usd": "45000.00", "market_cap": "850000000000"},
            {"symbol": "ETH", "name": "Ethereum", "price_usd": "2800.00", "market_cap": "340000000000"},
            {"symbol": "BNB", "name": "Binance Coin", "price_usd": "350.00", "market_cap": "55000000000"},
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            if sample_data:
                writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                writer.writeheader()
                writer.writerows(sample_data)

