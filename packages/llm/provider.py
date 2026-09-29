"""LLM Provider abstraction layer - vendor-agnostic interface."""

from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel
import json
import os
from packages.observability.logging import get_logger

logger = get_logger("llm")


class LLMMessage(BaseModel):
    role: str  # system, user, assistant
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str = ""
    usage: dict = {}
    finish_reason: str = ""


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """Send a chat completion request."""
        pass

    @abstractmethod
    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a chat request expecting JSON output."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible LLM provider (works with OpenAI, Azure, local servers)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.model = model
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")

        try:
            from openai import AsyncOpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = AsyncOpenAI(**kwargs)
        except ImportError:
            logger.warning("openai package not installed, using mock provider")
            self.client = None

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        if not self.client:
            return self._mock_response(messages)

        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await self.client.chat.completions.create(**kwargs)
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
                finish_reason=response.choices[0].finish_reason or "",
            )
        except Exception as e:
            logger.error("llm_request_failed", error=str(e))
            return self._mock_response(messages)

    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        response = await self.chat(
            messages, temperature, max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logger.warning("llm_json_parse_failed", content=response.content[:200])
            return {"error": "Failed to parse LLM JSON response", "raw": response.content}

    def _mock_response(self, messages: list[LLMMessage]) -> LLMResponse:
        """Fallback mock response when LLM is unavailable."""
        user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                user_msg = m.content
                break

        return LLMResponse(
            content=json.dumps({
                "answer": f"I received your question but the LLM service is not currently available. Your question was: '{user_msg[:100]}'. Please configure LLM_API_KEY in your .env file.",
                "intent": "UNKNOWN",
                "reasoning": "LLM service unavailable - using fallback response"
            }),
            model="mock",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            finish_reason="mock",
        )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            self.client = None

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(content="Anthropic client not available", model="mock")

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_msg,
                messages=chat_messages,
                temperature=temperature,
            )
            return LLMResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
                finish_reason=response.stop_reason or "",
            )
        except Exception as e:
            logger.error("anthropic_request_failed", error=str(e))
            return LLMResponse(content=f"LLM error: {str(e)}", model="error")

    async def chat_json(self, messages: list[LLMMessage], temperature: float = 0.1, max_tokens: int = 4096) -> dict:
        # Add JSON instruction to last user message
        if messages:
            last = messages[-1]
            messages = messages[:-1] + [LLMMessage(role=last.role, content=last.content + "\n\nRespond with valid JSON only.")]
        response = await self.chat(messages, temperature, max_tokens)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse", "raw": response.content}


def create_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """Factory function to create an LLM provider based on configuration."""
    provider_name = provider or os.getenv("LLM_PROVIDER", "openai")
    model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    if provider_name.lower() in ("openai", "azure", "local"):
        return OpenAIProvider(api_key=api_key, base_url=base_url, model=model_name)
    elif provider_name.lower() == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model_name)
    else:
        logger.warning(f"Unknown LLM provider '{provider_name}', defaulting to OpenAI-compatible")
        return OpenAIProvider(api_key=api_key, base_url=base_url, model=model_name)
