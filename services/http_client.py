"""HTTP client with retry logic and exponential backoff."""
import httpx
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from typing import Optional, Dict, Any
from core.config import settings
from core.logging_config import logger


class HTTPClient:
    """HTTP client with retry logic and rate limiting."""
    
    def __init__(self, rate_limiter=None):
        """
        Initialize HTTP client.
        
        Args:
            rate_limiter: Optional RateLimiter instance
        """
        self.rate_limiter = rate_limiter
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),  # Will use settings.MAX_RETRIES if needed
        wait=wait_exponential(multiplier=settings.RETRY_BACKOFF_FACTOR, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make GET request with retry logic.
        
        Args:
            url: Request URL
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            HTTP response
        """
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error",
                url=url,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("HTTP request failed, will retry", url=url, error=str(e))
            raise


async def get_with_retry(
    http_client: HTTPClient,
    url: str,
    source: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 3
) -> httpx.Response:
    """
    Reusable helper function for API calls with retry logic for HTTP 429 and 5xx errors.
    
    Retry logic:
    - Max retries: 3 (1 initial + 3 retries = 4 total attempts)
    - Backoff: 1s → 2s → 4s (exponential: 2^0, 2^1, 2^2)
    - Retry on: HTTP 429, HTTP 5xx
    
    Args:
        http_client: HTTPClient instance
        url: Request URL
        source: Source name for logging (e.g., 'coinpaprika', 'coingecko')
        headers: Optional headers
        params: Optional query parameters
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        HTTP response
        
    Raises:
        httpx.HTTPStatusError: If request fails after all retries
    """
    attempt = 0
    
    while attempt <= max_retries:
        try:
            response = await http_client.get(url, headers=headers, params=params)
            # Success - return response
            return response
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if e.response else 0
            
            # Check if we should retry based on status code
            should_retry = (
                status_code == 429 or  # Too Many Requests
                (500 <= status_code < 600)  # Server errors (5xx)
            )
            
            if not should_retry:
                # Don't retry on other status codes - raise immediately
                raise
            
            # If this is not the last attempt, retry
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "Retrying API request",
                    source=source,
                    attempt_number=attempt + 1,
                    wait_time=wait_time,
                    status_code=status_code,
                    url=url
                )
                await asyncio.sleep(wait_time)
                attempt += 1
                continue
            else:
                # Last attempt failed, raise the error
                raise
                
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            # For network errors, let the HTTPClient's retry logic handle it
            raise

