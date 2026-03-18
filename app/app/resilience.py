"""
Resilience patterns for external dependencies
"""
from functools import wraps
import asyncio
import time
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests fail fast without calling service
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        if self.state == "OPEN":
            if self.last_failure_time and \
               datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Will retry in {self.recovery_timeout} seconds"
            )


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """Decorator for circuit breaker pattern"""
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True,
    *args,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential: Use exponential backoff if True, fixed delay if False
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:
                # Calculate delay
                if exponential:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                else:
                    delay = base_delay
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                )
    
    raise last_exception


class ResourcePool:
    """
    Bulkhead pattern - limit concurrent access to expensive resources
    Prevents resource exhaustion and cascading failures
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.active_count = 0
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with resource pooling"""
        async with self.semaphore:
            self.active_count += 1
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            finally:
                self.active_count -= 1
    
    def get_available_slots(self) -> int:
        """Get number of available slots in pool"""
        return self.max_concurrent - self.active_count


class TimeoutManager:
    """Manage operation timeouts to prevent hanging requests"""
    
    @staticmethod
    async def execute_with_timeout(
        func: Callable,
        timeout_seconds: float,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with timeout"""
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Operation timed out after {timeout_seconds}s: {func.__name__}")
            raise TimeoutError(f"Operation exceeded {timeout_seconds}s timeout")


# Global resource pools for different services
llm_pool = ResourcePool(max_concurrent=5)  # Max 5 concurrent LLM calls
database_pool = ResourcePool(max_concurrent=20)  # Max 20 concurrent DB queries
fabric_pool = ResourcePool(max_concurrent=3)  # Max 3 concurrent Fabric API calls


# Circuit breakers for external services
azure_openai_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

database_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)

fabric_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)


async def resilient_llm_call(func: Callable, *args, **kwargs) -> Any:
    """
    Make LLM call with full resilience:
    - Resource pooling (prevent overload)
    - Circuit breaker (fail fast when service is down)
    - Retry with backoff (handle transient failures)
    - Timeout (prevent hanging)
    """
    async def protected_call():
        return await azure_openai_breaker.call_async(func, *args, **kwargs)
    
    async def retried_call():
        return await retry_with_backoff(
            protected_call,
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        )
    
    async def timed_call():
        return await TimeoutManager.execute_with_timeout(
            retried_call,
            timeout_seconds=30.0
        )
    
    return await llm_pool.execute(timed_call)


async def resilient_database_query(func: Callable, *args, **kwargs) -> Any:
    """
    Make database query with full resilience:
    - Resource pooling
    - Circuit breaker
    - Retry with backoff
    - Timeout
    """
    async def protected_call():
        return await database_breaker.call_async(func, *args, **kwargs)
    
    async def retried_call():
        return await retry_with_backoff(
            protected_call,
            max_attempts=3,
            base_delay=0.5,
            max_delay=5.0
        )
    
    async def timed_call():
        return await TimeoutManager.execute_with_timeout(
            retried_call,
            timeout_seconds=10.0
        )
    
    return await database_pool.execute(timed_call)
