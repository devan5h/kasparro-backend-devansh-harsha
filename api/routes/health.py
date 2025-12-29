"""Health check endpoint routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import get_db
from services.models import ETLRun, ETLStatus
from schemas.models import HealthResponse
from core.logging_config import logger
from datetime import datetime

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Checks:
    - Database connectivity
    - ETL last run status
    
    Returns:
        Health status with database and ETL information
    """
    # Check database connectivity
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error("Database health check failed", error=str(e))
    
    # Get last ETL run status
    etl_last_run = None
    try:
        # Check if etl_runs table exists by attempting to query it
        # This handles the case where migrations haven't run yet
        last_runs = db.query(ETLRun).order_by(ETLRun.started_at.desc()).limit(3).all()
        
        if last_runs:
            # Get the most recent run for each source
            sources_status = {}
            for run in last_runs:
                if run.source_name not in sources_status:
                    sources_status[run.source_name] = {
                        "source": run.source_name,
                        "status": run.status.value,
                        "started_at": run.started_at.isoformat(),
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "records_ingested": run.records_ingested,
                        "records_normalized": run.records_normalized,
                        "error_message": run.error_message,
                    }
            
            etl_last_run = {
                "last_runs": list(sources_status.values()),
                "overall_status": "healthy" if all(
                    s["status"] == ETLStatus.SUCCESS.value for s in sources_status.values()
                ) else "degraded"
            }
        else:
            # No ETL runs yet, but table exists
            etl_last_run = {
                "last_runs": [],
                "overall_status": "pending",
                "message": "No ETL runs have been executed yet"
            }
    except Exception as e:
        error_str = str(e)
        # Check if it's a table missing error
        if "does not exist" in error_str or "UndefinedTable" in error_str:
            logger.warning("ETL tables not found - migrations may not have run", error=error_str)
            etl_last_run = {
                "error": "Database migrations not applied. Please ensure migrations have run.",
                "status": "pending_migrations"
            }
        else:
            logger.warning("Failed to fetch ETL run status", error=error_str)
            etl_last_run = {"error": error_str}
    
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        database=db_status,
        etl_last_run=etl_last_run
    )

