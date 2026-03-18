"""OpenAI-compatible provider (also supports vLLM)."""

from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI

from spq.providers.base import LLMProvider, LLMResponse, Message


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API and any OpenAI-compatible endpoint (vLLM, etc.)."""

    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        provider_name: str = "openai",
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self._provider_name = provider_name
        api_key = os.environ.get(api_key_env, "")
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

    @property
    def name(self) -> str:
        return self._provider_name

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [self._to_api_message(m) for m in messages],
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if self.sampling.temperature is not None:
            kwargs["temperature"] = self.sampling.temperature
        if self.sampling.top_p is not None:
            kwargs["top_p"] = self.sampling.top_p
        if self.sampling.max_tokens is not None:
            kwargs["max_tokens"] = self.sampling.max_tokens

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls_data = None
        if message.tool_calls:
            tool_calls_data = []
            for tc in message.tool_calls:
                tool_calls_data.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls_data,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "",
        )

    @staticmethod
    def _to_api_message(msg: Message) -> dict[str, Any]:
        d: dict[str, Any] = {"role": msg.role}
        if msg.content is not None:
            d["content"] = msg.content
        if msg.tool_call_id is not None:
            d["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls is not None:
            d["tool_calls"] = msg.tool_calls
        if msg.name is not None:
            d["name"] = msg.name
        return d
