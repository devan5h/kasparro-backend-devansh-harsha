"""Base ingester class for ETL pipeline."""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from services.models import ETLRun, ETLStatus
from services.checkpoint_manager import CheckpointManager
from datetime import datetime
from typing import Optional, Dict, Any
from core.logging_config import logger
import json


class BaseIngester(ABC):
    """Base class for all data ingesters."""
    
    def __init__(self, db: Session, source_name: str):
        """
        Initialize base ingester.
        
        Args:
            db: Database session
            source_name: Name of the data source
        """
        self.db = db
        self.source_name = source_name
        self.checkpoint_manager = CheckpointManager(db)
        self.current_run: Optional[ETLRun] = None
    
    def start_run(self) -> ETLRun:
        """
        Start a new ETL run.
        
        Returns:
            ETLRun instance
        """
        self.current_run = ETLRun(
            source_name=self.source_name,
            status=ETLStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self.db.add(self.current_run)
        self.db.commit()
        logger.info("ETL run started", source=self.source_name, run_id=self.current_run.id)
        return self.current_run
    
    def complete_run(self, records_ingested: int = 0, records_normalized: int = 0, last_successful_timestamp: Optional[datetime] = None):
        """
        Mark ETL run as successful and update checkpoint.
        
        Args:
            records_ingested: Number of records ingested
            records_normalized: Number of records normalized
            last_successful_timestamp: Latest timestamp from successfully processed records
        """
        if self.current_run:
            self.current_run.status = ETLStatus.SUCCESS
            self.current_run.completed_at = datetime.utcnow()
            self.current_run.records_ingested = records_ingested
            self.current_run.records_normalized = records_normalized
            self.db.commit()
            
            # Update checkpoint ONLY on success with last successful timestamp
            if last_successful_timestamp:
                self.checkpoint_manager.update_checkpoint_on_success(
                    source_name=self.source_name,
                    last_successful_timestamp=last_successful_timestamp,
                    last_run_id=self.current_run.id
                )
            
            logger.info(
                "ETL run completed",
                source=self.source_name,
                run_id=self.current_run.id,
                ingested=records_ingested,
                normalized=records_normalized,
                last_timestamp=last_successful_timestamp.isoformat() if last_successful_timestamp else None
            )
    
    def fail_run(self, error_message: str):
        """
        Mark ETL run as failed.
        
        Args:
            error_message: Error message
        """
        if self.current_run:
            self.current_run.status = ETLStatus.FAILED
            self.current_run.completed_at = datetime.utcnow()
            self.current_run.error_message = error_message
            self.db.commit()
            logger.error(
                "ETL run failed",
                source=self.source_name,
                run_id=self.current_run.id,
                error=error_message
            )
    
    @abstractmethod
    async def ingest(self) -> Dict[str, int]:
        """
        Perform ingestion.
        
        Returns:
            Dictionary with 'ingested' and 'normalized' counts
        """
        pass
    
    def save_raw_data(self, raw_data: Dict[str, Any], source_id: Optional[str] = None):
        """
        Save raw data to appropriate raw table.
        
        Args:
            raw_data: Raw data dictionary
            source_id: Optional source identifier
        """
        # This will be implemented by subclasses
        pass

