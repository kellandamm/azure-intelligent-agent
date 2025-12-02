"""OpenTelemetry configuration for distributed tracing."""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor

from config import settings
from utils.logging_config import logger


def setup_telemetry():
    """Configure OpenTelemetry with Azure Monitor."""
    try:
        if not settings.enable_tracing:
            logger.info("📊 Tracing is disabled")
            return
        
        # For local development without Application Insights, skip telemetry setup
        # Azure Monitor configuration requires APPLICATIONINSIGHTS_CONNECTION_STRING environment variable
        if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
            logger.info("📊 Application Insights not configured (fine for local development)")
            return
        
        # Configure Azure Monitor (Application Insights)
        configure_azure_monitor()
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        
        logger.info("✅ OpenTelemetry configured successfully")
    
    except Exception as e:
        logger.warning(f"⚠️  Failed to setup telemetry: {e}")


def instrument_fastapi(app):
    """Instrument FastAPI application for tracing."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented for tracing")
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument FastAPI: {e}")
