"""
Comprehensive observability infrastructure
"""
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import structlog
import time
import uuid
from datetime import datetime
from typing import Optional
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Custom metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status']
)

agent_invocations = Counter(
    'agent_invocations_total',
    'Total agent invocations',
    ['agent_type', 'status']
)

token_usage = Counter(
    'llm_token_usage_total',
    'Total LLM tokens used',
    ['model', 'type']  # type: prompt/completion
)

active_sessions = Gauge(
    'active_user_sessions',
    'Number of active user sessions'
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query latency',
    ['query_type']
)

cache_operations = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'status']  # operation: get/set/delete, status: hit/miss/error
)

authentication_attempts = Counter(
    'authentication_attempts_total',
    'Authentication attempts',
    ['method', 'status']  # method: jwt/apikey, status: success/failure
)

from starlette.middleware.base import BaseHTTPMiddleware

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Track all requests with rich context"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Structured logging context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            user_id=getattr(request.state, 'user_id', None),
            path=request.url.path,
            method=request.method
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).observe(duration)
            
            # Log successful request
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                user_agent=request.headers.get('user-agent', 'unknown')
            )
            
            # Add correlation ID to response
            response.headers['X-Correlation-ID'] = correlation_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration=duration
            )
            raise
        finally:
            # Clear context for next request
            structlog.contextvars.clear_contextvars()


def track_agent_invocation(agent_type: str, status: str, token_count: Optional[int] = None, 
                           model: Optional[str] = None, duration: Optional[float] = None):
    """Track agent invocation metrics"""
    agent_invocations.labels(agent_type=agent_type, status=status).inc()
    
    if token_count and model:
        token_usage.labels(model=model, type="completion").inc(token_count)
    
    logger.info(
        "agent_invocation",
        agent_type=agent_type,
        status=status,
        token_count=token_count,
        model=model,
        duration=duration
    )


def track_database_query(query_type: str, duration: float, success: bool):
    """Track database query metrics"""
    database_query_duration.labels(query_type=query_type).observe(duration)
    
    logger.debug(
        "database_query",
        query_type=query_type,
        duration=duration,
        success=success
    )


def track_cache_operation(operation: str, status: str):
    """Track cache operations"""
    cache_operations.labels(operation=operation, status=status).inc()


def track_authentication(method: str, status: str, user_id: Optional[str] = None):
    """Track authentication attempts"""
    authentication_attempts.labels(method=method, status=status).inc()
    
    logger.info(
        "authentication_attempt",
        method=method,
        status=status,
        user_id=user_id
    )


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Pre-configured Application Insights queries for monitoring dashboards
KUSTO_QUERIES = {
    "error_rate": """
        requests
        | where timestamp > ago(1h)
        | summarize 
            total = count(),
            errors = countif(success == false)
        | extend error_rate = errors * 100.0 / total
    """,
    
    "slowest_endpoints": """
        requests
        | where timestamp > ago(1h)
        | summarize 
            avg_duration = avg(duration),
            p95_duration = percentile(duration, 95),
            p99_duration = percentile(duration, 99)
            by name
        | order by p95_duration desc
        | take 10
    """,
    
    "agent_performance": """
        traces
        | where message == "agent_invocation"
        | where timestamp > ago(1h)
        | extend agent = tostring(customDimensions.agent_type)
        | summarize 
            count = count(),
            avg_tokens = avg(todouble(customDimensions.token_count)),
            avg_duration = avg(todouble(customDimensions.duration)),
            success_rate = 100.0 * countif(customDimensions.status == "success") / count()
            by agent
    """,
    
    "user_activity": """
        traces
        | where message == "request_completed"
        | where timestamp > ago(24h)
        | extend user_id = tostring(customDimensions.user_id)
        | where isnotempty(user_id)
        | summarize 
            request_count = count(),
            unique_paths = dcount(tostring(customDimensions.path))
            by user_id
        | order by request_count desc
        | take 20
    """,
    
    "cache_effectiveness": """
        traces
        | where message == "cache_operation"
        | where timestamp > ago(1h)
        | extend operation = tostring(customDimensions.operation)
        | extend status = tostring(customDimensions.status)
        | summarize 
            hits = countif(status == "hit"),
            misses = countif(status == "miss"),
            errors = countif(status == "error")
        | extend hit_rate = 100.0 * hits / (hits + misses)
    """,
    
    "authentication_failures": """
        traces
        | where message == "authentication_attempt"
        | where timestamp > ago(1h)
        | where customDimensions.status == "failure"
        | extend method = tostring(customDimensions.method)
        | summarize count = count() by method, bin(timestamp, 5m)
        | order by timestamp desc
    """
}
