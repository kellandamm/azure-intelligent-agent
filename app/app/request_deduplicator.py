"""
Request Deduplication Manager
Prevents duplicate agent calls from concurrent requests, retries, and double-clicks
"""
import asyncio
import hashlib
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestDeduplicator:
    """
    Prevents duplicate processing of identical requests within a time window.
    
    Use cases:
    - User double-clicks Send button
    - Network retry with same message
    - Concurrent requests from multiple tabs
    """
    
    def __init__(self, window_seconds: int = 10):
        """
        Initialize request deduplicator.
        
        Args:
            window_seconds: Time window for deduplication (default: 10 seconds)
        """
        self.window_seconds = window_seconds
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"✅ Request deduplicator initialized (window: {window_seconds}s)")
    
    def _generate_request_id(
        self,
        thread_id: str,
        message: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Generate unique request ID from request parameters.
        
        Args:
            thread_id: Conversation thread ID
            message: User message content
            user_id: Optional user identifier
            
        Returns:
            Unique request ID (hash)
        """
        # Create deterministic ID from request parameters
        components = [
            str(thread_id or "no-thread"), 
            str(message), 
            str(user_id or "anonymous")
        ]
        content = "|".join(components)
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def check_duplicate(
        self,
        thread_id: str,
        message: str,
        user_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is a duplicate within the time window.
        
        Args:
            thread_id: Conversation thread ID
            message: User message content
            user_id: Optional user identifier
            
        Returns:
            Tuple of (is_duplicate, request_id)
            - is_duplicate: True if this is a duplicate request
            - request_id: Unique identifier for this request
        """
        request_id = self._generate_request_id(thread_id, message, user_id)
        current_time = time.time()
        
        async with self._lock:
            # Clean up expired requests
            expired = [
                req_id for req_id, data in self._active_requests.items()
                if current_time - data["timestamp"] > self.window_seconds
            ]
            for req_id in expired:
                del self._active_requests[req_id]
            
            # Check if request is already being processed
            if request_id in self._active_requests:
                request_data = self._active_requests[request_id]
                age = current_time - request_data["timestamp"]
                
                logger.warning(
                    f"🔁 Duplicate request detected: {request_id} "
                    f"(age: {age:.1f}s, thread: {thread_id[:8]}...)"
                )
                
                return True, request_id
            
            # Register new request
            self._active_requests[request_id] = {
                "timestamp": current_time,
                "thread_id": thread_id,
                "message": message[:100],  # Store truncated message for debugging
                "user_id": user_id
            }
            
            logger.debug(f"✅ New request registered: {request_id}")
            return False, request_id
    
    async def mark_complete(self, request_id: str) -> bool:
        """
        Mark request as complete and remove from active tracking.
        
        Args:
            request_id: Request identifier returned from check_duplicate
            
        Returns:
            True if request was found and removed
        """
        async with self._lock:
            if request_id in self._active_requests:
                del self._active_requests[request_id]
                logger.debug(f"✅ Request completed: {request_id}")
                return True
            
            return False
    
    async def wait_for_completion(
        self,
        request_id: str,
        timeout_seconds: int = 30,
        poll_interval: float = 0.5
    ) -> bool:
        """
        Wait for a duplicate request to complete.
        
        Args:
            request_id: Request identifier to wait for
            timeout_seconds: Maximum time to wait
            poll_interval: How often to check (seconds)
            
        Returns:
            True if request completed, False if timed out
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            async with self._lock:
                if request_id not in self._active_requests:
                    logger.debug(f"✅ Duplicate request completed: {request_id}")
                    return True
            
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"⏰ Timeout waiting for duplicate request: {request_id}")
        return False
    
    async def get_active_count(self) -> int:
        """Get number of currently active requests."""
        async with self._lock:
            return len(self._active_requests)
    
    async def get_active_requests(self) -> list[Dict[str, Any]]:
        """
        Get list of currently active requests (for monitoring).
        
        Returns:
            List of active request info
        """
        current_time = time.time()
        
        async with self._lock:
            return [
                {
                    "request_id": req_id,
                    "thread_id": data["thread_id"],
                    "message_preview": data["message"],
                    "age_seconds": current_time - data["timestamp"],
                    "user_id": data.get("user_id")
                }
                for req_id, data in self._active_requests.items()
            ]


# Context manager for automatic cleanup
class DeduplicationContext:
    """
    Context manager for request deduplication with automatic cleanup.
    
    Usage:
        async with DeduplicationContext(deduplicator, thread_id, message, user_id):
            # Process request
            response = await process_chat(message)
            return response
    """
    
    def __init__(
        self,
        deduplicator: RequestDeduplicator,
        thread_id: str,
        message: str,
        user_id: Optional[str] = None
    ):
        self.deduplicator = deduplicator
        self.thread_id = thread_id
        self.message = message
        self.user_id = user_id
        self.request_id: Optional[str] = None
        self.is_duplicate = False
    
    async def __aenter__(self):
        """Check for duplicate on entry."""
        self.is_duplicate, self.request_id = await self.deduplicator.check_duplicate(
            self.thread_id,
            self.message,
            self.user_id
        )
        
        if self.is_duplicate:
            raise DuplicateRequestError(
                f"Duplicate request detected (ID: {self.request_id})",
                request_id=self.request_id
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Mark complete on exit."""
        if self.request_id:
            await self.deduplicator.mark_complete(self.request_id)
        
        return False  # Don't suppress exceptions


class DuplicateRequestError(Exception):
    """Raised when a duplicate request is detected."""
    
    def __init__(self, message: str, request_id: str):
        super().__init__(message)
        self.request_id = request_id
