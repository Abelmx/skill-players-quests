"""Multi-turn conversation manager."""

from __future__ import annotations

import json
import logging
from typing import Any

from spq.core.models import (
    ActivationMode,
    ConversationTurn,
    ExecutionTrace,
    TaskDef,
    ToolCall,
)
from spq.providers.base import TOOL_SCHEMAS, LLMProvider, LLMResponse, Message
from spq.runtime.executor import ToolExecutor

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages the multi-turn conversation loop for one task execution."""

    def __init__(
        self,
        provider: LLMProvider,
        executor: ToolExecutor,
        max_turns: int = 10,
    ) -> None:
        self.provider = provider
        self.executor = executor
        self.max_turns = max_turns

    async def run(
        self,
        system_prompt: str,
        task: TaskDef,
        mode: ActivationMode,
    ) -> ExecutionTrace:
        trace = ExecutionTrace(
            task_id=task.id,
            provider_name=self.provider.name,
            model_name=self.provider.model,
            activation_mode=mode,
        )

        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=task.query),
        ]

        for turn_idx in range(self.max_turns):
            try:
                response = await self.provider.chat(messages, tools=TOOL_SCHEMAS)
            except Exception as e:
                logger.error("LLM call failed on turn %d: %s", turn_idx, e)
                trace.error = str(e)
                break

            turn = ConversationTurn(
                assistant_text=response.content or "",
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )
            trace.total_input_tokens += response.input_tokens
            trace.total_output_tokens += response.output_tokens

            if not response.tool_calls:
                turn.tool_calls = []
                trace.turns.append(turn)
                trace.final_output = response.content or ""
                break

            assistant_msg = Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
                reasoning_content=response.reasoning_content,
            )
            messages.append(assistant_msg)

            for tc_data in response.tool_calls:
                tool_call = await self._process_tool_call(tc_data, trace)
                turn.tool_calls.append(tool_call)

                messages.append(Message(
                    role="tool",
                    content=tool_call.result,
                    tool_call_id=tc_data["id"],
                ))

            trace.turns.append(turn)

            if response.finish_reason == "stop":
                trace.final_output = response.content or ""
                break
        else:
            logger.warning("Task %s hit max_turns (%d)", task.id, self.max_turns)
            if trace.turns:
                trace.final_output = trace.turns[-1].assistant_text

        return trace

    async def _process_tool_call(
        self,
        tc_data: dict[str, Any],
        trace: ExecutionTrace,
    ) -> ToolCall:
        func = tc_data["function"]
        tool_name = func["name"]
        try:
            arguments = json.loads(func["arguments"])
        except (json.JSONDecodeError, TypeError):
            arguments = {"raw": func["arguments"]}

        result = await self.executor.execute(tool_name, arguments)

        call = ToolCall(tool_name=tool_name, arguments=arguments, result=result)
        trace.record_tool_call(call)

        logger.debug("Tool %s(%s) -> %s", tool_name, arguments, result[:200])
        return call
