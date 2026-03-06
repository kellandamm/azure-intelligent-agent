"""
GraphRAG Proxy Routes - Forward authenticated requests to GraphRAG service
This file should be added to: C:\code\agentsdemos\app\routes_graphrag_proxy.py
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Dict, Any
import logging

from utils.auth import get_current_user, require_permission

logger = logging.getLogger(__name__)

# GraphRAG service URL - configure in Azure App Service settings
GRAPHRAG_SERVICE_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")

graphrag_proxy_router = APIRouter(
    prefix="/api/graphrag",
    tags=["GraphRAG Proxy"],
    dependencies=[Depends(get_current_user)]  # All routes require authentication
)


async def proxy_request(
    path: str,
    method: str = "GET",
    body: Dict[Any, Any] = None,
    current_user: dict = None
):
    """Proxy request to GraphRAG service with authentication context"""
    url = f"{GRAPHRAG_SERVICE_URL}/api/{path}"
    
    username = current_user.get('username', 'unknown') if current_user else 'unknown'
    logger.info(f"Proxying {method} request to {url} for user {username}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=body)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # Log the response status
            logger.info(f"GraphRAG responded with status {response.status_code}")
            
            # Return the response
            if response.status_code >= 200 and response.status_code < 300:
                return JSONResponse(
                    content=response.json() if response.text else {},
                    status_code=response.status_code
                )
            else:
                logger.error(f"GraphRAG error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GraphRAG service error: {response.text}"
                )
                
        except httpx.TimeoutException:
            logger.error("Timeout connecting to GraphRAG service")
            raise HTTPException(status_code=504, detail="GraphRAG service timeout")
        except httpx.RequestError as e:
            logger.error(f"Error connecting to GraphRAG service: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"GraphRAG service unavailable. Check GRAPHRAG_SERVICE_URL configuration."
            )


@graphrag_proxy_router.get("/health")
async def graphrag_health(current_user: dict = Depends(get_current_user)):
    """
    Proxy health check to GraphRAG service.
    Requires user authentication.
    """
    return await proxy_request("health", method="GET", current_user=current_user)


@graphrag_proxy_router.post("/query")
async def graphrag_query(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy query request to GraphRAG service.
    Requires user authentication.
    """
    body = await request.json()
    logger.info(f"GraphRAG query from user {current_user.get('username')}: {body.get('query', '')[:50]}")
    return await proxy_request("query", method="POST", body=body, current_user=current_user)


@graphrag_proxy_router.post("/search")
async def graphrag_search(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy search request to GraphRAG service.
    Requires user authentication.
    """
    body = await request.json()
    logger.info(f"GraphRAG search from user {current_user.get('username')}: {body.get('query', '')[:50]}")
    return await proxy_request("search", method="POST", body=body, current_user=current_user)


@graphrag_proxy_router.get("/stats")
async def graphrag_stats(current_user: dict = Depends(get_current_user)):
    """
    Proxy graph statistics request to GraphRAG service.
    Requires user authentication.
    """
    return await proxy_request("graph/stats", method="GET", current_user=current_user)


@graphrag_proxy_router.get("/export")
async def graphrag_export(current_user: dict = Depends(get_current_user)):
    """
    Proxy graph export request to GraphRAG service.
    Requires user authentication.
    """
    return await proxy_request("graph/export", method="GET", current_user=current_user)


@graphrag_proxy_router.post("/ingest")
async def graphrag_ingest(
    request: Request,
    current_user: dict = Depends(require_permission("manage_agents"))
):
    """
    Proxy document ingest request to GraphRAG service.
    Requires admin permission.
    """
    body = await request.json()
    logger.info(f"GraphRAG ingest from admin {current_user.get('username')}: {len(body.get('documents', []))} documents")
    return await proxy_request("ingest", method="POST", body=body, current_user=current_user)


@graphrag_proxy_router.post("/upload")
async def graphrag_upload(
    request: Request,
    current_user: dict = Depends(require_permission("manage_agents"))
):
    """
    Proxy file upload request to GraphRAG service.
    Requires admin permission.
    """
    body = await request.json()
    logger.info(f"GraphRAG upload from admin {current_user.get('username')}")
    return await proxy_request("upload", method="POST", body=body, current_user=current_user)


@graphrag_proxy_router.post("/reload")
async def graphrag_reload(current_user: dict = Depends(require_permission("manage_agents"))):
    """
    Proxy graph reload request to GraphRAG service.
    Requires admin permission.
    """
    logger.info(f"GraphRAG reload requested by admin {current_user.get('username')}")
    return await proxy_request("graph/reload", method="POST", body={}, current_user=current_user)


@graphrag_proxy_router.post("/compare")
async def graphrag_compare(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy RAG comparison request to GraphRAG service.
    Requires user authentication.
    """
    body = await request.json()
    return await proxy_request("compare", method="POST", body=body, current_user=current_user)
