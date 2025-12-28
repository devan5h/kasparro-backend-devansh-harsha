"""Script to run ETL pipeline."""
import asyncio
import sys
from core.database import SessionLocal
from services.etl_runner import ETLRunner
from core.logging_config import logger


async def main():
    """Run ETL pipeline."""
    db = SessionLocal()
    try:
        runner = ETLRunner(db)
        
        # Check if running in continuous mode
        if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
            await runner.run_continuous()
        else:
            results = await runner.run_all()
            logger.info("ETL run completed", results=results)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

