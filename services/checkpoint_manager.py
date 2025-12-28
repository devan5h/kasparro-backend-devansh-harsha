"""Checkpoint management for incremental ingestion."""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from services.models import ETLCheckpoint
from typing import Optional, Dict, Any
from datetime import datetime
import json
from core.logging_config import logger


class CheckpointManager:
    """Manages checkpoints for incremental ETL ingestion."""
    
    def __init__(self, db: Session):
        """
        Initialize checkpoint manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_checkpoint(self, source_name: str) -> Optional[ETLCheckpoint]:
        """
        Get checkpoint for a source.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Checkpoint if exists, None otherwise
        """
        return self.db.query(ETLCheckpoint).filter(
            ETLCheckpoint.source_name == source_name
        ).first()
    
    def update_checkpoint(
        self,
        source_name: str,
        last_ingested_id: Optional[str] = None,
        last_ingested_timestamp: Optional[datetime] = None,
        checkpoint_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update or create checkpoint (for intermediate progress tracking).
        
        Args:
            source_name: Name of the data source
            last_ingested_id: Last processed ID
            last_ingested_timestamp: Last processed timestamp
            checkpoint_data: Additional checkpoint data
        """
        checkpoint = self.get_checkpoint(source_name)
        
        if checkpoint:
            if last_ingested_id is not None:
                checkpoint.last_ingested_id = last_ingested_id
            if last_ingested_timestamp is not None:
                checkpoint.last_ingested_timestamp = last_ingested_timestamp
            if checkpoint_data is not None:
                checkpoint.checkpoint_data = json.dumps(checkpoint_data)
            checkpoint.updated_at = datetime.utcnow()
        else:
            checkpoint = ETLCheckpoint(
                source_name=source_name,
                last_ingested_id=last_ingested_id,
                last_ingested_timestamp=last_ingested_timestamp,
                checkpoint_data=json.dumps(checkpoint_data) if checkpoint_data else None
            )
            self.db.add(checkpoint)
        
        self.db.commit()
        logger.info("Checkpoint updated", source=source_name, last_id=last_ingested_id)
    
    def update_checkpoint_on_success(
        self,
        source_name: str,
        last_successful_timestamp: datetime,
        last_run_id: int,
        last_ingested_id: Optional[str] = None,
        checkpoint_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update checkpoint ONLY on successful ETL completion.
        This is the authoritative checkpoint that enables incremental ingestion.
        
        Args:
            source_name: Name of the data source
            last_successful_timestamp: Last successfully processed timestamp
            last_run_id: ID of the successful ETL run
            last_ingested_id: Last processed ID (optional)
            checkpoint_data: Additional checkpoint data (optional)
        """
        checkpoint = self.get_checkpoint(source_name)
        
        if checkpoint:
            checkpoint.last_successful_timestamp = last_successful_timestamp
            checkpoint.last_run_id = last_run_id
            if last_ingested_id is not None:
                checkpoint.last_ingested_id = last_ingested_id
            if checkpoint_data is not None:
                checkpoint.checkpoint_data = json.dumps(checkpoint_data)
            checkpoint.updated_at = datetime.utcnow()
        else:
            checkpoint = ETLCheckpoint(
                source_name=source_name,
                last_successful_timestamp=last_successful_timestamp,
                last_run_id=last_run_id,
                last_ingested_id=last_ingested_id,
                checkpoint_data=json.dumps(checkpoint_data) if checkpoint_data else None
            )
            self.db.add(checkpoint)
        
        self.db.commit()
        logger.info(
            "Checkpoint updated on success",
            source=source_name,
            last_successful_timestamp=last_successful_timestamp.isoformat(),
            last_run_id=last_run_id
        )
    
    def get_checkpoint_data(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint data as dictionary.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Checkpoint data dictionary or None
        """
        checkpoint = self.get_checkpoint(source_name)
        if checkpoint and checkpoint.checkpoint_data:
            try:
                return json.loads(checkpoint.checkpoint_data)
            except json.JSONDecodeError:
                return None
        return None

