"""
Azure AI Content Safety integration for prompt injection detection.
Provides AI-powered prompt injection detection with regex fallback.
"""
import logging
import re
from typing import Optional, Tuple
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)


class ContentSafetyValidator:
    """
    Content safety validator with AI-powered prompt injection detection.
    Falls back to regex patterns if Azure AI Content Safety is unavailable.
    """

    def __init__(
        self,
        content_safety_endpoint: Optional[str] = None,
        content_safety_key: Optional[str] = None,
        enable_ai_detection: bool = True,
    ):
        """
        Initialize content safety validator.

        Args:
            content_safety_endpoint: Azure AI Content Safety endpoint URL
            content_safety_key: Azure AI Content Safety API key
            enable_ai_detection: Whether to use AI detection (requires endpoint/key)
        """
        self.enable_ai_detection = enable_ai_detection and content_safety_endpoint and content_safety_key
        self.client: Optional[ContentSafetyClient] = None

        if self.enable_ai_detection:
            try:
                self.client = ContentSafetyClient(
                    content_safety_endpoint, AzureKeyCredential(content_safety_key)
                )
                logger.info("✅ Azure AI Content Safety initialized")
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to initialize Azure AI Content Safety, using regex fallback: {e}"
                )
                self.enable_ai_detection = False
        else:
            logger.info("ℹ️ Azure AI Content Safety disabled, using regex-only validation")

        # Regex patterns for prompt injection detection (fallback)
        self.dangerous_patterns = [
            # Direct instruction override
            r"ignore\s+(previous|all\s+previous|the\s+above)",
            r"disregard\s+(instructions|previous|all)",
            r"override\s+(instructions|settings|rules)",
            r"forget\s+(everything|all|previous)",
            
            # Mode switching attacks
            r"(admin|developer|god|debug|root)\s+mode",
            r"enable\s+(admin|developer|god|debug)",
            r"switch\s+to\s+(admin|developer|god)",
            
            # System prompt leakage attempts
            r"(show|reveal|display|print)\s+(system\s+prompt|instructions)",
            r"what\s+(is|are)\s+your\s+(instructions|system\s+prompt)",
            r"repeat\s+your\s+(instructions|system\s+prompt)",
            
            # Role play attacks
            r"you\s+are\s+now\s+a\s+(different|new)",
            r"act\s+as\s+(if|though)\s+you",
            r"pretend\s+(to\s+be|you\s+are)",
            
            # Jailbreak attempts
            r"jailbreak",
            r"do\s+anything\s+now",
            r"DAN\s+mode",
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns
        ]

    async def validate_prompt(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate message for prompt injection attempts.

        Args:
            message: User message to validate

        Returns:
            Tuple of (is_safe, reason)
            - is_safe: True if message is safe, False if suspicious
            - reason: Description of why message was flagged (None if safe)
        """
        # First try AI-powered detection if available
        if self.enable_ai_detection and self.client:
            try:
                ai_result = await self._check_with_ai(message)
                if ai_result is not None:
                    return ai_result
            except Exception as e:
                logger.warning(f"AI content safety check failed, falling back to regex: {e}")

        # Fallback to regex patterns
        return self._check_with_regex(message)

    async def _check_with_ai(self, message: str) -> Optional[Tuple[bool, Optional[str]]]:
        """
        Check message using Azure AI Content Safety.
        
        Returns None if service unavailable, otherwise (is_safe, reason).
        """
        try:
            # Analyze text for prompt injection attacks
            request = AnalyzeTextOptions(text=message)
            
            response = self.client.analyze_text(request)
            
            # Check for high-risk categories
            # Note: Prompt injection might be detected under different categories
            # depending on the content safety model version
            for category_analysis in response.categories_analysis:
                if category_analysis.severity >= 4:  # High or Critical severity
                    reason = f"Content flagged by AI: {category_analysis.category} (severity {category_analysis.severity})"
                    logger.warning(f"🚨 {reason}")
                    return (False, reason)
            
            logger.debug("✅ AI content safety check passed")
            return (True, None)
            
        except AzureError as e:
            logger.error(f"Azure AI Content Safety error: {e}")
            return None  # Fall back to regex
        except Exception as e:
            logger.error(f"Unexpected error in AI content safety: {e}")
            return None

    def _check_with_regex(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Check message using regex patterns (fallback method).

        Returns:
            Tuple of (is_safe, reason)
        """
        message_lower = message.lower()

        # Check each pattern
        for i, pattern in enumerate(self.compiled_patterns):
            match = pattern.search(message_lower)
            if match:
                matched_text = match.group(0)
                reason = f"Potential prompt injection detected: '{matched_text}'"
                logger.warning(f"🚨 {reason}")
                return (False, reason)

        logger.debug("✅ Regex content safety check passed")
        return (True, None)

    def sanitize_message(self, message: str) -> str:
        """
        Sanitize message by removing control characters.

        Args:
            message: Message to sanitize

        Returns:
            Sanitized message
        """
        # Remove control characters except newlines and tabs
        sanitized = "".join(
            char for char in message if ord(char) >= 32 or char in ("\n", "\t")
        )
        return sanitized.strip()
