"""
Token Management and Conversation History Limiting
Prevents token overflow errors by managing conversation history size
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages conversation history to prevent token limit overflow"""
    
    # Maximum tokens to allow in conversation history
    # GPT-4o has 128K context, but we reserve space for:
    # - System prompts (~1K)
    # - Tool definitions (~2K)
    # - Response generation (~4K)
    # Safe limit: 100K tokens for history
    MAX_HISTORY_TOKENS = 100_000
    
    # Simple message count limit (quick fix for demos)
    MAX_MESSAGES = 20  # Keep last 20 messages (10 exchanges)
    
    # Rough token estimation (more accurate would use tiktoken)
    AVG_TOKENS_PER_MESSAGE = 200
    
    @staticmethod
    def truncate_history_simple(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simple truncation: Keep only the last N messages.
        
        This is a quick fix to prevent crashes during demos.
        System messages are always preserved.
        
        Args:
            messages: Full conversation history
            
        Returns:
            Truncated history with system messages + recent conversation
        """
        if len(messages) <= TokenManager.MAX_MESSAGES:
            return messages
        
        # Separate system messages from conversation
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        conversation = [msg for msg in messages if msg.get("role") != "system"]
        
        # Keep last N conversation messages
        recent_conversation = conversation[-TokenManager.MAX_MESSAGES:]
        
        # Combine system + recent conversation
        truncated = system_messages + recent_conversation
        
        logger.info(
            f"🔄 Truncated conversation history: {len(messages)} → {len(truncated)} messages "
            f"(kept {len(system_messages)} system + {len(recent_conversation)} conversation)"
        )
        
        return truncated
    
    @staticmethod
    def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for message list.
        
        This is a rough estimate. For production, use tiktoken library:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4")
            tokens = len(encoding.encode(text))
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Estimated token count
        """
        total_chars = sum(
            len(str(msg.get("content", ""))) 
            for msg in messages
        )
        
        # Rough approximation: 1 token ≈ 4 characters
        estimated_tokens = total_chars // 4
        
        return estimated_tokens
    
    @staticmethod
    def truncate_by_tokens(
        messages: List[Dict[str, Any]],
        max_tokens: int = MAX_HISTORY_TOKENS
    ) -> List[Dict[str, Any]]:
        """
        Truncate history based on estimated token count.
        
        More accurate than message count, but still uses estimation.
        For production, integrate tiktoken library.
        
        Args:
            messages: Full conversation history
            max_tokens: Maximum tokens to keep
            
        Returns:
            Truncated history within token limit
        """
        if not messages:
            return []
        
        # Always preserve system messages
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        conversation = [msg for msg in messages if msg.get("role") != "system"]
        
        system_tokens = TokenManager.estimate_tokens(system_messages)
        available_tokens = max_tokens - system_tokens
        
        if available_tokens <= 0:
            logger.warning("⚠️ System messages exceed token limit!")
            return system_messages[:1]  # Keep only first system message
        
        # Build history from most recent backwards
        kept_messages = []
        current_tokens = 0
        
        for msg in reversed(conversation):
            msg_tokens = TokenManager.estimate_tokens([msg])
            
            if current_tokens + msg_tokens > available_tokens:
                break
            
            kept_messages.insert(0, msg)
            current_tokens += msg_tokens
        
        truncated = system_messages + kept_messages
        
        logger.info(
            f"🔄 Token-based truncation: {len(messages)} → {len(truncated)} messages "
            f"(~{current_tokens + system_tokens} tokens)"
        )
        
        return truncated
    
    @staticmethod
    def should_compress(messages: List[Dict[str, Any]]) -> bool:
        """
        Check if conversation history should be compressed/summarized.
        
        Args:
            messages: Conversation history
            
        Returns:
            True if compression recommended
        """
        if len(messages) > TokenManager.MAX_MESSAGES:
            return True
        
        estimated_tokens = TokenManager.estimate_tokens(messages)
        if estimated_tokens > TokenManager.MAX_HISTORY_TOKENS * 0.8:  # 80% threshold
            return True
        
        return False
    
    @staticmethod
    def create_summary_placeholder(
        original_count: int,
        summarized_count: int
    ) -> Dict[str, Any]:
        """
        Create a placeholder message indicating summarization occurred.
        
        Args:
            original_count: Original message count
            summarized_count: Number of messages summarized
            
        Returns:
            System message explaining the summarization
        """
        return {
            "role": "system",
            "content": (
                f"[Previous conversation summary: {summarized_count} messages from earlier in "
                f"this conversation were summarized to manage context length. "
                f"Total messages: {original_count}]"
            ),
            "metadata": {
                "type": "summary_placeholder",
                "original_count": original_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    async def summarize_conversation(
        messages: List[Dict[str, Any]],
        client: Any,
        keep_recent: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Intelligently summarize old conversation messages using LLM.
        
        Instead of simple truncation, we use the LLM to create a concise summary
        of older messages, preserving important context while reducing tokens.
        
        Args:
            messages: Full conversation history
            client: Azure OpenAI client instance
            keep_recent: Number of recent messages to keep as-is (default: 10)
            
        Returns:
            Compressed history: [system messages] + [summary] + [recent messages]
        """
        if len(messages) <= keep_recent:
            return messages
        
        # Separate message types
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        conversation = [msg for msg in messages if msg.get("role") != "system"]
        
        if len(conversation) <= keep_recent:
            return messages
        
        # Split conversation into old and recent
        old_messages = conversation[:-keep_recent]
        recent_messages = conversation[-keep_recent:]
        
        logger.info(
            f"🤖 Generating conversation summary: "
            f"{len(old_messages)} old messages → summary"
        )
        
        try:
            # Prepare old messages for summarization
            conversation_text = "\n\n".join([
                f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
                for msg in old_messages
            ])
            
            # Call LLM to generate summary
            summary_prompt = f"""You are helping manage a long conversation by creating a concise summary.

Below is the earlier part of a conversation between a user and an AI assistant. 
Please create a brief summary (3-5 paragraphs) that captures:
1. Key topics discussed
2. Important decisions or information shared
3. Any context needed to understand the recent conversation
4. User preferences or requirements mentioned

Conversation to summarize ({len(old_messages)} messages):
{conversation_text}

Provide ONLY the summary, no additional commentary."""
            
            # Make async API call
            response = await client.chat.completions.create(
                model="gpt-5.2",  # Use same model as orchestrator
                messages=[
                    {"role": "system", "content": "You create concise, accurate conversation summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent summaries
                max_tokens=500  # Limit summary length
            )
            
            summary_content = response.choices[0].message.content
            
            # Create summary message
            summary_message = {
                "role": "system",
                "content": f"[Conversation Summary - Earlier Messages]\n\n{summary_content}\n\n[End of Summary - Recent conversation continues below]",
                "metadata": {
                    "type": "conversation_summary",
                    "summarized_count": len(old_messages),
                    "original_count": len(messages),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Combine: system messages + summary + recent conversation
            result = system_messages + [summary_message] + recent_messages
            
            logger.info(
                f"✅ Conversation summarized: {len(messages)} → {len(result)} messages "
                f"({len(old_messages)} summarized, {len(recent_messages)} recent kept)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate summary, falling back to truncation: {e}")
            # Fallback to simple truncation if summarization fails
            return system_messages + recent_messages


# ===================================================================
# Usage Examples
# ===================================================================

"""
# In agent_framework_manager.py:

from app.token_manager import TokenManager

class AgentFrameworkManager:
    async def chat(self, message: str, thread_id: str = None) -> ChatResult:
        # Get session history
        session_history = self.sessions.get(thread_id, [])
        
        # Check if conversation needs compression
        if TokenManager.should_compress(session_history):
            # NEW: Use LLM-based summarization instead of simple truncation
            session_history = await TokenManager.summarize_conversation(
                session_history,
                client=self.client,
                keep_recent=10
            )
        
        # Add new message
        session_history.append({"role": "user", "content": message})
        
        # Continue with agent processing...
        response = await self._run_orchestrator(session_history)
        
        return response
"""
