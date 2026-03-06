"""
Multi-level caching strategy using CosmosDB
"""
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from functools import wraps
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)


class CosmosDBCache:
    """
    CosmosDB-based caching layer
    
    Benefits over Redis:
    - Native Azure integration
    - Automatic indexing and querying
    - TTL support built-in
    - Multi-region replication
    - Lower cost for infrequent access patterns
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        self.database = None
        self.container = None
        
        try:
            endpoint = os.getenv("COSMOSDB_ENDPOINT")
            key = os.getenv("COSMOSDB_KEY")
            database_name = os.getenv("COSMOSDB_DATABASE", "cache")
            container_name = os.getenv("COSMOSDB_CONTAINER", "app_cache")
            
            if endpoint and key:
                self.client = CosmosClient(endpoint, credential=key)
                
                # Create database if not exists
                self.database = self.client.create_database_if_not_exists(id=database_name)
                
                # Create container with TTL enabled
                self.container = self.database.create_container_if_not_exists(
                    id=container_name,
                    partition_key=PartitionKey(path="/category"),
                    default_ttl=-1  # Enable TTL, items specify their own TTL
                )
                
                self.enabled = True
                logger.info("CosmosDB cache initialized successfully")
            else:
                logger.warning("CosmosDB cache not configured - caching disabled")
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB cache: {e}")
            self.enabled = False
    
    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Retrieve value from cache"""
        if not self.enabled:
            return None
        
        try:
            from app.observability import track_cache_operation
            
            item = self.container.read_item(
                item=key,
                partition_key=category
            )
            
            # Check if expired (CosmosDB TTL may not have cleaned up yet)
            if 'expires_at' in item:
                expires_at = datetime.fromisoformat(item['expires_at'])
                if datetime.utcnow() > expires_at:
                    track_cache_operation("get", "expired")
                    self.delete(key, category)
                    return None
            
            track_cache_operation("get", "hit")
            logger.debug(f"Cache hit: {key}")
            
            return item.get('value')
            
        except exceptions.CosmosResourceNotFoundError:
            from app.observability import track_cache_operation
            track_cache_operation("get", "miss")
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            from app.observability import track_cache_operation
            track_cache_operation("get", "error")
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        category: str = "default",
        ttl_seconds: int = 3600
    ):
        """Store value in cache with TTL"""
        if not self.enabled:
            return
        
        try:
            from app.observability import track_cache_operation
            
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            item = {
                'id': key,
                'category': category,
                'value': value,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'ttl': ttl_seconds  # CosmosDB will auto-delete after this
            }
            
            self.container.upsert_item(item)
            track_cache_operation("set", "success")
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            
        except Exception as e:
            from app.observability import track_cache_operation
            track_cache_operation("set", "error")
            logger.error(f"Cache set error for {key}: {e}")
    
    async def delete(self, key: str, category: str = "default"):
        """Delete value from cache"""
        if not self.enabled:
            return
        
        try:
            from app.observability import track_cache_operation
            
            self.container.delete_item(
                item=key,
                partition_key=category
            )
            track_cache_operation("delete", "success")
            logger.debug(f"Cache delete: {key}")
            
        except exceptions.CosmosResourceNotFoundError:
            pass  # Already deleted
        except Exception as e:
            from app.observability import track_cache_operation
            track_cache_operation("delete", "error")
            logger.error(f"Cache delete error for {key}: {e}")
    
    async def invalidate_pattern(self, pattern: str, category: str = "default"):
        """Invalidate all cache entries matching pattern in category"""
        if not self.enabled:
            return
        
        try:
            # Query items matching pattern
            query = f"SELECT c.id FROM c WHERE c.category = @category AND CONTAINS(c.id, @pattern)"
            items = list(self.container.query_items(
                query=query,
                parameters=[
                    {"name": "@category", "value": category},
                    {"name": "@pattern", "value": pattern}
                ],
                enable_cross_partition_query=False
            ))
            
            # Delete matching items
            for item in items:
                await self.delete(item['id'], category)
            
            logger.info(f"Invalidated {len(items)} cache entries matching pattern: {pattern}")
            
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")
    
    async def clear_category(self, category: str = "default"):
        """Clear all items in a category"""
        if not self.enabled:
            return
        
        try:
            query = "SELECT c.id FROM c WHERE c.category = @category"
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@category", "value": category}],
                enable_cross_partition_query=False
            ))
            
            for item in items:
                await self.delete(item['id'], category)
            
            logger.info(f"Cleared {len(items)} items from category: {category}")
            
        except Exception as e:
            logger.error(f"Cache clear category error: {e}")


# Global cache instance
cache_manager = CosmosDBCache()


def hash_args(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    ttl_seconds: int = 3600,
    category: str = "default",
    key_prefix: str = ""
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl_seconds=3600, category="agent_config", key_prefix="config")
        async def get_agent_configuration(agent_key: str):
            return load_agent_configs()[agent_key]
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function args
            args_hash = hash_args(*args, **kwargs)
            cache_key = f"{key_prefix}:{func.__name__}:{args_hash}" if key_prefix else f"{func.__name__}:{args_hash}"
            
            # Try cache first
            cached_result = await cache_manager.get(cache_key, category)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Store in cache (don't await to avoid blocking)
            await cache_manager.set(cache_key, result, category, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# Pre-configured cache categories and TTLs
CACHE_PROFILES = {
    "agent_config": {
        "category": "agent_config",
        "ttl": 3600  # 1 hour - agent configs change infrequently
    },
    "fabric_data": {
        "category": "fabric_data",
        "ttl": 300  # 5 minutes - data changes more frequently
    },
    "user_profile": {
        "category": "user_profile",
        "ttl": 1800  # 30 minutes
    },
    "powerbi_embed": {
        "category": "powerbi_embed",
        "ttl": 3600  # 1 hour - embed tokens have 1hr expiry anyway
    },
    "conversation": {
        "category": "conversation",
        "ttl": 7200  # 2 hours - conversation history
    }
}


# Usage example imports
import asyncio
