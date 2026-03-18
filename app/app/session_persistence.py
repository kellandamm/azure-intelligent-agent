"""
Session Persistence Manager for CosmosDB
Enables durable session storage across app restarts and horizontal scaling
"""
import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionPersistenceManager:
    """
    Manages conversation sessions with CosmosDB persistence.
    
    Benefits:
    - Sessions survive app restarts
    - Enables horizontal scaling (multiple app instances)
    - Automatic TTL cleanup via CosmosDB
    - Query capabilities for analytics
    """
    
    def __init__(self, cache_manager=None, session_ttl_seconds: int = 3600):
        """
        Initialize session persistence manager.
        
        Args:
            cache_manager: CosmosDBCache instance
            session_ttl_seconds: Session expiration time (default: 1 hour)
        """
        self.cache_manager = cache_manager
        self.session_ttl_seconds = session_ttl_seconds
        self.enabled = cache_manager and cache_manager.enabled
        
        # In-memory cache for performance (write-through pattern)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        if self.enabled:
            logger.info("✅ Session persistence enabled (CosmosDB)")
        else:
            logger.info("ℹ️ Session persistence disabled (in-memory only)")
    
    async def get_session(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session from cache or CosmosDB.
        
        Args:
            thread_id: Unique thread identifier
            
        Returns:
            Session data dict or None if not found
        """
        # Check memory cache first
        async with self._lock:
            if thread_id in self._memory_cache:
                session = self._memory_cache[thread_id]
                # Update last access time
                session["last_access"] = time.time()
                return session
        
        # Fall back to CosmosDB if enabled
        if self.enabled:
            try:
                session_data = await self.cache_manager.get(
                    key=f"session:{thread_id}",
                    category="sessions"
                )
                
                if session_data:
                    # Restore to memory cache
                    async with self._lock:
                        self._memory_cache[thread_id] = session_data
                        session_data["last_access"] = time.time()
                    
                    logger.debug(f"Session loaded from CosmosDB: {thread_id}")
                    return session_data
            except Exception as e:
                logger.error(f"Error loading session from CosmosDB: {e}")
        
        return None
    
    async def save_session(
        self,
        thread_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save session to memory and CosmosDB.
        
        Args:
            thread_id: Unique thread identifier
            messages: Conversation message history
            metadata: Optional metadata (user_id, agent_type, etc.)
            
        Returns:
            True if saved successfully
        """
        session_data = {
            "thread_id": thread_id,
            "messages": messages,
            "last_access": time.time(),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Save to memory cache
        async with self._lock:
            self._memory_cache[thread_id] = session_data
        
        # Persist to CosmosDB if enabled
        if self.enabled:
            try:
                await self.cache_manager.set(
                    key=f"session:{thread_id}",
                    value=session_data,
                    category="sessions",
                    ttl_seconds=self.session_ttl_seconds
                )
                logger.debug(f"Session persisted to CosmosDB: {thread_id}")
                return True
            except Exception as e:
                logger.error(f"Error saving session to CosmosDB: {e}")
                return False
        
        return True
    
    async def delete_session(self, thread_id: str) -> bool:
        """
        Delete session from memory and CosmosDB.
        
        Args:
            thread_id: Unique thread identifier
            
        Returns:
            True if deleted successfully
        """
        # Remove from memory cache
        async with self._lock:
            if thread_id in self._memory_cache:
                del self._memory_cache[thread_id]
        
        # Delete from CosmosDB if enabled
        if self.enabled:
            try:
                await self.cache_manager.delete(
                    key=f"session:{thread_id}",
                    category="sessions"
                )
                logger.debug(f"Session deleted from CosmosDB: {thread_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting session from CosmosDB: {e}")
                return False
        
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from memory cache.
        CosmosDB TTL handles automatic cleanup in persistent storage.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_count = 0
        current_time = time.time()
        
        async with self._lock:
            expired_threads = [
                thread_id
                for thread_id, session_data in self._memory_cache.items()
                if current_time - session_data.get("last_access", 0) > self.session_ttl_seconds
            ]
            
            for thread_id in expired_threads:
                del self._memory_cache[thread_id]
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"🧹 Cleaned up {expired_count} expired session(s) from memory")
        
        return expired_count
    
    async def get_session_count(self) -> int:
        """Get current number of active sessions in memory."""
        async with self._lock:
            return len(self._memory_cache)
    
    async def list_active_sessions(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List active sessions with basic info.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        async with self._lock:
            sessions = []
            for thread_id, session_data in list(self._memory_cache.items())[:limit]:
                sessions.append({
                    "thread_id": thread_id,
                    "message_count": len(session_data.get("messages", [])),
                    "last_access": session_data.get("last_access"),
                    "age_seconds": time.time() - session_data.get("last_access", 0),
                    "metadata": session_data.get("metadata", {})
                })
            
            return sorted(sessions, key=lambda x: x["last_access"], reverse=True)
