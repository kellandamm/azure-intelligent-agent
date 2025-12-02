"""Minimal Azure OpenAI client wrapper used for local development.

This stub emulates the small subset of the `agent_framework.azure` module that
our demo hub relies on. It performs direct HTTP calls against the Azure OpenAI
Chat Completions API using an Azure credential or API key.
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
import inspect
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from azure.core.exceptions import HttpResponseError

_DEFAULT_SCOPE = "https://cognitiveservices.azure.com/.default"
_DEFAULT_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")


@dataclass
class ChatResponseUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ToolCallDescriptor:
    id: str
    name: str
    arguments: str


@dataclass
class ChatCompletionMessage:
    role: str
    text: str
    tool_calls: List[ToolCallDescriptor]


@dataclass
class ChatResponse:
    messages: List[ChatCompletionMessage]
    usage: Optional[ChatResponseUsage]
    raw_response: Dict[str, Any]


def _sanitize_env_value(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.strip().strip('"').strip("'").rstrip('/')


class AzureOpenAIChatClient:
    """Lightweight chat client that mimics the Agent Framework surface area."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        credential: Any = None,
        api_version: Optional[str] = None,
        default_temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> None:
        self.endpoint = _sanitize_env_value(endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        self.deployment_name = _sanitize_env_value(
            deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        )
        self.api_version = api_version or _DEFAULT_API_VERSION
        self.credential = credential
        self.default_temperature = default_temperature
        self.timeout = timeout
        key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.api_key = _sanitize_env_value(key) if key else None

        if not self.endpoint:
            raise RuntimeError("Azure OpenAI endpoint is required. Set AZURE_OPENAI_ENDPOINT.")
        if not self.deployment_name:
            raise RuntimeError(
                "Azure OpenAI deployment name is required. Set AZURE_OPENAI_DEPLOYMENT."
            )
        if not self.api_key and credential is None:
            raise RuntimeError(
                "No Azure credential available. Provide a credential or set AZURE_OPENAI_KEY."
            )

        self._token_lock = asyncio.Lock()
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0.0

    async def _get_bearer_token(self) -> str:
        if self.api_key:
            return ""

        async with self._token_lock:
            now = time.time()
            if self._cached_token and now < self._token_expiry - 60:
                return self._cached_token

            if self.credential is None:
                raise RuntimeError("Azure credential is required for token acquisition.")

            token = await asyncio.to_thread(self.credential.get_token, _DEFAULT_SCOPE)
            self._cached_token = token.token
            self._token_expiry = float(token.expires_on)
            return token.token

    async def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
            return headers

        token = await self._get_bearer_token()
        headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _submit_chat_request(
        self,
        *,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_output_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions"
        params = {"api-version": self.api_version}
        payload: Dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
        }
        if max_output_tokens:
            payload["max_output_tokens"] = max_output_tokens
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        headers = await self._build_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)

        if response.status_code >= 400:
            raise HttpResponseError(message=response.text, status_code=response.status_code)

        return response.json()
    
    async def complete_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        temp = temperature if temperature is not None else self.default_temperature
        return await self._submit_chat_request(
            messages=messages,
            temperature=temp,
            tools=tools,
            tool_choice=tool_choice,
        )

    async def get_response(
        self,
        *,
        messages: List[Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> ChatResponse:
        """Mimic Agent Framework ChatResponse behavior for the demo."""

        api_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if hasattr(msg, "to_dict"):
                api_messages.append(msg.to_dict())
            elif isinstance(msg, dict):
                content = msg.get("content") or msg.get("text")
                api_messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": content,
                    }
                )
            else:
                raise TypeError(f"Unsupported message type: {type(msg)!r}")

        normalized_tools: Optional[List[Dict[str, Any]]] = None
        if tools:
            normalized_tools = []
            for tool in tools:
                if isinstance(tool, dict):
                    normalized_tools.append(tool)
                    continue
                if callable(tool):
                    tool_name = getattr(tool, "__name__", "tool_function")
                    description = inspect.getdoc(tool) or f"Tool function {tool_name}"
                    sig = inspect.signature(tool)
                    properties: Dict[str, Any] = {}
                    required: List[str] = []
                    for param_name, param in sig.parameters.items():
                        properties[param_name] = {
                            "type": "string",
                            "description": f"Argument '{param_name}'"
                        }
                        if param.default is inspect._empty:
                            required.append(param_name)
                    normalized_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": description,
                                "parameters": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required,
                                },
                            },
                        }
                    )
                else:
                    continue
            if not normalized_tools:
                normalized_tools = None

        payload = await self.complete_with_tools(
            messages=api_messages,
            tools=normalized_tools,
            temperature=temperature,
            tool_choice=tool_choice if normalized_tools else "none",
        )

        messages_out: List[ChatCompletionMessage] = []
        for choice in payload.get("choices", []):
            message_payload = choice.get("message") or {}
            role = message_payload.get("role", "assistant")
            content = message_payload.get("content")
            if isinstance(content, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            else:
                text = content or ""

            tool_calls_payload = message_payload.get("tool_calls") or []
            tool_calls: List[ToolCallDescriptor] = []
            for call in tool_calls_payload:
                function_payload = call.get("function") or {}
                tool_calls.append(
                    ToolCallDescriptor(
                        id=call.get("id") or "",
                        name=function_payload.get("name") or "",
                        arguments=function_payload.get("arguments") or "{}",
                    )
                )

            messages_out.append(
                ChatCompletionMessage(
                    role=role,
                    text=text,
                    tool_calls=tool_calls,
                )
            )

        usage_payload = payload.get("usage") or {}
        usage: Optional[ChatResponseUsage] = None
        if usage_payload:
            usage = ChatResponseUsage(
                prompt_tokens=int(usage_payload.get("prompt_tokens", 0)),
                completion_tokens=int(usage_payload.get("completion_tokens", 0)),
                total_tokens=int(usage_payload.get("total_tokens", 0)),
            )

        return ChatResponse(
            messages=messages_out,
            usage=usage,
            raw_response=payload,
        )
