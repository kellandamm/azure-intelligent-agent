"""
Rate limiting middleware for API endpoints.
Prevents brute force attacks and API abuse.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self):
        """Initialize rate limiter with storage."""
        # Store: {ip_address: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory bloat."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Keep last hour
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (ts, ep) for ts, ep in self.requests[ip] 
                if ts > cutoff_time
            ]
            # Remove IP if no recent requests
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
        logger.debug(f"Rate limiter cleanup: {len(self.requests)} IPs tracked")
    
    def check_rate_limit(
        self, 
        ip_address: str, 
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            ip_address: Client IP address
            endpoint: API endpoint being accessed
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if within limit, raises HTTPException if exceeded
        """
        self._cleanup_old_requests()
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Get recent requests from this IP for this endpoint
        recent_requests = [
            ts for ts, ep in self.requests[ip_address]
            if ts > cutoff_time and ep == endpoint
        ]
        
        if len(recent_requests) >= max_requests:
            # Calculate retry time
            oldest_request = min(recent_requests)
            retry_after = int(oldest_request + window_seconds - current_time)
            
            logger.warning(
                f"Rate limit exceeded for {ip_address} on {endpoint}: "
                f"{len(recent_requests)} requests in {window_seconds}s"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record this request
        self.requests[ip_address].append((current_time, endpoint))
        return True
    
    def get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        Handles X-Forwarded-For header for proxies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check X-Forwarded-For header (if behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain (original client)
            return forwarded.split(",")[0].strip()
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "/api/auth/login": (5, 60),        # 5 attempts per minute
    "/api/auth/register": (3, 3600),   # 3 registrations per hour
    "/api/chat": (30, 60),             # 30 chat messages per minute
    "/api/admin": (50, 60),            # 50 admin requests per minute
}


async def check_rate_limit(request: Request) -> bool:
    """
    Rate limit dependency for FastAPI endpoints.
    
    Usage:
        @app.post("/api/endpoint", dependencies=[Depends(check_rate_limit)])
        async def my_endpoint():
            ...
    """
    client_ip = rate_limiter.get_client_ip(request)
    endpoint_path = request.url.path
    
    # Find matching rate limit config
    for pattern, (max_requests, window) in RATE_LIMITS.items():
        if endpoint_path.startswith(pattern):
            return rate_limiter.check_rate_limit(
                client_ip, 
                endpoint_path,
                max_requests,
                window
            )
    
    # Default rate limit for unmatched endpoints
    return rate_limiter.check_rate_limit(
        client_ip,
        endpoint_path,
        max_requests=100,
        window_seconds=60
    )
