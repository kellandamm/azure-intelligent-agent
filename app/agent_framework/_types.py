"""Type definitions for agent framework stub."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TextContent:
    """Text content wrapper."""
    text: str


@dataclass
class ChatMessage:
    """Chat message with role and content."""
    role: str
    content: List[TextContent]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary format for API calls."""
        result = {
            "role": self.role,
            "content": self.content[0].text if self.content else "",
        }
        
        # Include tool_calls for assistant messages
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        
        # Include tool_call_id for tool messages
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        return result
