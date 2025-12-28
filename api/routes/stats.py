"""Stats endpoint routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from core.database import get_db
from services.models import ETLRun, ETLStatus
from schemas.models import StatsResponse
from core.logging_config import logger

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    source: Optional[str] = Query(None, description="Filter by source name"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent runs to return"),
    db: Session = Depends(get_db)
):
    """
    Get ETL run statistics.
    
    Returns:
        ETL run summaries and statistics
    """
    try:
        # Build query
        query = db.query(ETLRun)
        
        if source:
            query = query.filter(ETLRun.source_name == source.lower())
        
        # Get all runs for statistics
        all_runs = query.all()
        
        # Calculate statistics
        total_runs = len(all_runs)
        successful_runs = len([r for r in all_runs if r.status == ETLStatus.SUCCESS])
        failed_runs = len([r for r in all_runs if r.status == ETLStatus.FAILED])
        
        # Get last run
        last_run = None
        if all_runs:
            latest = max(all_runs, key=lambda r: r.started_at)
            last_run = {
                "id": latest.id,
                "source": latest.source_name,
                "status": latest.status.value,
                "started_at": latest.started_at.isoformat(),
                "completed_at": latest.completed_at.isoformat() if latest.completed_at else None,
                "records_ingested": latest.records_ingested,
                "records_normalized": latest.records_normalized,
                "error_message": latest.error_message,
            }
        
        # Get recent runs
        recent_runs_query = query.order_by(desc(ETLRun.started_at)).limit(limit)
        recent_runs = recent_runs_query.all()
        
        runs_data = []
        for run in recent_runs:
            runs_data.append({
                "id": run.id,
                "source": run.source_name,
                "status": run.status.value,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "records_ingested": run.records_ingested,
                "records_normalized": run.records_normalized,
                "error_message": run.error_message,
            })
        
        logger.info("Stats requested", total_runs=total_runs, source=source)
        
        return StatsResponse(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            last_run=last_run,
            runs=runs_data
        )
    
    except Exception as e:
        logger.error("Error fetching stats", error=str(e))
        raise

