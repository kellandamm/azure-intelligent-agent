"""
Comprehensive health check endpoints
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import pyodbc
import os
from typing import Dict, Any
import asyncio
import time

router = APIRouter()

async def check_database() -> Dict[str, Any]:
    """Check database connectivity and responsiveness"""
    start_time = time.time()
    try:
        # Get database connection string
        server = os.getenv("SQL_SERVER")
        database = os.getenv("SQL_DATABASE")
        
        if not server or not database:
            return {
                "status": "unhealthy",
                "error": "Database configuration missing",
                "latency_ms": 0
            }
        
        conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server={server};Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=5;"
        
        if os.getenv("SQL_USE_AZURE_AUTH") == "true":
            # Check if running in Azure and use Authentication=ActiveDirectoryMsi
            is_azure_environment = any([
                os.getenv('WEBSITE_INSTANCE_ID'),
                os.getenv('IDENTITY_ENDPOINT'),
                os.getenv('MSI_ENDPOINT')
            ])
            
            if is_azure_environment:
                # Running in Azure - use Managed Identity (driver handles authentication)
                conn_str += "Authentication=ActiveDirectoryMsi;"
                conn = pyodbc.connect(conn_str)
            else:
                # Local development - use access token
                from azure.identity import DefaultAzureCredential
                import struct
                
                credential = DefaultAzureCredential()
                token = credential.get_token("https://database.windows.net/.default")
                token_bytes = token.token.encode('utf-8')
                token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
                conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
        else:
            username = os.getenv("SQL_USERNAME")
            password = os.getenv("SQL_PASSWORD")
            if username and password:
                conn_str += f"UID={username};PWD={password};"
                conn = pyodbc.connect(conn_str)
            else:
                return {
                    "status": "unhealthy",
                    "error": "Database credentials missing",
                    "latency_ms": 0
                }
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "server": server,
            "database": database
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round(latency, 2)
        }


async def check_azure_openai() -> Dict[str, Any]:
    """Check Azure OpenAI connectivity"""
    start_time = time.time()
    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not deployment:
            return {
                "status": "unhealthy",
                "error": "Azure OpenAI configuration missing",
                "latency_ms": 0
            }
        
        # Use managed identity if no API key is provided
        if not api_key:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider
            )
        else:
            client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=api_key
            )
        
        # Simple test call
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "endpoint": endpoint,
            "deployment": deployment
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round(latency, 2)
        }


async def check_cosmosdb_cache() -> Dict[str, Any]:
    """Check CosmosDB cache connectivity"""
    start_time = time.time()
    try:
        from azure.cosmos import CosmosClient
        
        endpoint = os.getenv("COSMOSDB_ENDPOINT")
        
        if not endpoint:
            return {
                "status": "not_configured",
                "message": "CosmosDB cache not configured",
                "latency_ms": 0
            }
        
        client = CosmosClient(endpoint, credential=os.getenv("COSMOSDB_KEY"))
        database = client.get_database_client(os.getenv("COSMOSDB_DATABASE", "cache"))
        
        # Simple connectivity check
        list(database.list_containers(max_item_count=1))
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "endpoint": endpoint
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round(latency, 2)
        }


@router.get("/health")
async def health_check():
    """Basic liveness check - returns 200 if service is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Azure Intelligent Agent"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Detailed readiness check - verifies all dependencies
    Returns 200 if service is ready to accept requests
    Returns 503 if any critical dependency is unhealthy
    """
    # Run all checks in parallel
    checks = await asyncio.gather(
        check_database(),
        check_azure_openai(),
        check_cosmosdb_cache(),
        return_exceptions=True
    )
    
    database_check, openai_check, cache_check = checks
    
    # Build response
    health_checks = {
        "database": database_check if not isinstance(database_check, Exception) else {
            "status": "unhealthy",
            "error": str(database_check)
        },
        "azure_openai": openai_check if not isinstance(openai_check, Exception) else {
            "status": "unhealthy",
            "error": str(openai_check)
        },
        "cosmosdb_cache": cache_check if not isinstance(cache_check, Exception) else {
            "status": "unhealthy",
            "error": str(cache_check)
        }
    }
    
    # Determine overall status
    critical_checks = [health_checks["database"], health_checks["azure_openai"]]
    all_critical_healthy = all(
        check["status"] == "healthy" 
        for check in critical_checks
    )
    
    overall_status = "healthy" if all_critical_healthy else "unhealthy"
    
    # Cache is optional, mark as degraded if it's down
    if health_checks["cosmosdb_cache"]["status"] == "unhealthy" and overall_status == "healthy":
        overall_status = "degraded"
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": health_checks
    }
    
    # Return 503 if unhealthy (for load balancer health checks)
    status_code = 200 if overall_status in ["healthy", "degraded"] else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response, status_code=status_code)


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness check
    Returns 200 if the application process is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/startup")
async def startup_check():
    """
    Kubernetes-style startup check
    Returns 200 once the application has finished initialization
    """
    # Check critical components are initialized
    try:
        # Verify environment variables are loaded
        required_vars = ["AZURE_OPENAI_ENDPOINT", "SQL_SERVER", "JWT_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "error": f"Missing configuration: {', '.join(missing_vars)}"
                },
                status_code=503
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "status": "not_ready",
                "error": str(e)
            },
            status_code=503
        )
