"""
Rate Limiting Middleware
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.buckets: Dict[str, Tuple[int, datetime]] = {}
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        async with self.lock:
            now = datetime.now()
            
            if key not in self.buckets:
                self.buckets[key] = (self.burst - 1, now)
                return True
            
            tokens, last_update = self.buckets[key]
            
            # Refill tokens based on time passed
            time_passed = (now - last_update).total_seconds()
            tokens_to_add = int(time_passed * (self.requests_per_minute / 60))
            tokens = min(self.burst, tokens + tokens_to_add)
            
            if tokens > 0:
                self.buckets[key] = (tokens - 1, now)
                return True
            else:
                self.buckets[key] = (0, last_update)
                return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute=requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Use IP address as key (or user_id if authenticated)
        client_ip = request.client.host
        
        # Check rate limit
        if not await self.limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        return response
