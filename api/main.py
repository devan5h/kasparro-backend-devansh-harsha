"""FastAPI application main file."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import data, health, stats
from core.logging_config import logger
from core.database import SessionLocal
from services.models import ETLRun, ETLStatus
from sqlalchemy import and_
from datetime import datetime

app = FastAPI(
    title="Kasparoo Backend API",
    description="Production-grade backend + ETL system for cryptocurrency data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(stats.router, prefix="/api", tags=["stats"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Kasparoo Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "data": "/api/data",
            "stats": "/api/stats"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Log application startup and cleanup interrupted ETL runs."""
    logger.info("Kasparoo Backend API started")
    
    # Cleanup interrupted ETL runs (status='running' but completed_at is NULL)
    db = SessionLocal()
    try:
        interrupted_runs = db.query(ETLRun).filter(
            and_(
                ETLRun.status == ETLStatus.RUNNING,
                ETLRun.completed_at.is_(None)
            )
        ).all()
        
        if interrupted_runs:
            for run in interrupted_runs:
                run.status = ETLStatus.FAILED
                run.error_message = 'Interrupted due to restart'
                run.completed_at = datetime.utcnow()
            
            db.commit()
            logger.info(
                "Cleaned up interrupted ETL runs",
                count=len(interrupted_runs),
                run_ids=[r.id for r in interrupted_runs]
            )
    except Exception as e:
        logger.error("Failed to cleanup interrupted ETL runs", error=str(e))
        db.rollback()
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Kasparoo Backend API shutting down")

