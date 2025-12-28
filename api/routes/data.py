"""Data endpoint routes."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
from datetime import datetime
import time
import uuid
from core.database import get_db
from services.models import MarketData, Coin
from schemas.models import DataResponse
from core.logging_config import logger

router = APIRouter()


@router.get("/data", response_model=DataResponse)
async def get_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by coin symbol"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get market data with pagination and filtering.
    
    Returns:
        Paginated market data with metadata
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Build query
        query = db.query(MarketData).join(Coin, MarketData.coin_id == Coin.id)
        
        # Apply filters
        if symbol:
            query = query.filter(Coin.symbol.ilike(f"%{symbol.upper()}%"))
        
        if source:
            query = query.filter(MarketData.source == source.lower())
        
        if start_date:
            query = query.filter(MarketData.timestamp >= start_date)
        
        if end_date:
            query = query.filter(MarketData.timestamp <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        market_data = query.order_by(MarketData.timestamp.desc()).offset(offset).limit(page_size).all()
        
        # Format response data
        data = []
        for md in market_data:
            coin = md.coin
            data.append({
                "id": md.id,
                "coin": {
                    "id": coin.id,
                    "symbol": coin.symbol,
                    "name": coin.name,
                },
                "price_usd": float(md.price_usd),
                "market_cap_usd": float(md.market_cap_usd) if md.market_cap_usd else None,
                "volume_24h_usd": float(md.volume_24h_usd) if md.volume_24h_usd else None,
                "price_change_24h": float(md.price_change_24h) if md.price_change_24h else None,
                "timestamp": md.timestamp.isoformat(),
                "source": md.source,
                "created_at": md.created_at.isoformat(),
            })
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # Calculate API latency
        api_latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Data request completed",
            request_id=request_id,
            page=page,
            page_size=page_size,
            total_count=total_count,
            latency_ms=api_latency_ms
        )
        
        return DataResponse(
            metadata={
                "request_id": request_id,
                "api_latency_ms": api_latency_ms
            },
            data=data,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        )
    
    except Exception as e:
        logger.error("Error fetching data", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

