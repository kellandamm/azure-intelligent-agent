"""OpenTelemetry configuration for distributed tracing."""
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Wrap azure-monitor import to handle version incompatibility
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    AZURE_MONITOR_AVAILABLE = True
except ImportError as e:
    AZURE_MONITOR_AVAILABLE = False
    print(f"⚠️ Azure Monitor OpenTelemetry import failed: {e}")
    print("⚠️ Telemetry will be disabled. This is OK for local development.")

from config import settings
from utils.logging_config import logger


def setup_telemetry():
    """Configure OpenTelemetry with Azure Monitor and Live Metrics."""
    try:
        if not settings.enable_tracing:
            logger.info("📊 Tracing is disabled")
            return
        
        if not AZURE_MONITOR_AVAILABLE:
            logger.warning("📊 Azure Monitor OpenTelemetry not available - telemetry disabled")
            return
        
        # For local development without Application Insights, skip telemetry setup
        # Azure Monitor configuration requires APPLICATIONINSIGHTS_CONNECTION_STRING environment variable
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logger.info("📊 Application Insights not configured (fine for local development)")
            return
        
        # Configure Azure Monitor (Application Insights) with Live Metrics enabled
        configure_azure_monitor(
            connection_string=connection_string,
            enable_live_metrics=True,  # Enable Live Metrics Stream
            logger_name="agent_framework",
            # Collect additional performance counters
            instrumentation_options={
                "azure_sdk": {"enabled": True},
                "django": {"enabled": False},
                "fastapi": {"enabled": True},
                "flask": {"enabled": False},
                "psycopg2": {"enabled": False},
                "requests": {"enabled": True},
                "sqlalchemy": {"enabled": False},
                "urllib": {"enabled": True},
                "urllib3": {"enabled": True},
            }
        )
        
        # Set up tracer provider (configure_azure_monitor does this, but we ensure it)
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace.set_tracer_provider(TracerProvider())
        
        logger.info("✅ OpenTelemetry configured successfully with Live Metrics enabled")
        logger.info(f"📡 Live Metrics Stream: Enabled for connection {connection_string[:50]}...")
    
    except Exception as e:
        logger.warning(f"⚠️  Failed to setup telemetry: {e}")


def instrument_fastapi(app):
    """Instrument FastAPI application for tracing."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented for tracing")
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument FastAPI: {e}")
