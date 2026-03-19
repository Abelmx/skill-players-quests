"""Core data models for the evaluation framework."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ActivationMode(str, Enum):
    CATALOG = "catalog"
    FULL_INJECT = "full_inject"


class SkillMeta(BaseModel):
    """Parsed metadata from a SKILL.md frontmatter."""

    name: str
    description: str
    location: Path
    base_dir: Path
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    body: str = ""


class TaskDef(BaseModel):
    """A single evaluation task definition loaded from YAML."""

    id: str
    name: str
    category: str
    query: str
    available_skills: list[str]
    expected_skills: list[str]
    expected_actions: list[dict[str, Any]] = Field(default_factory=list)
    oracle: dict[str, str]
    difficulty: str = "medium"
    tags: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """A single tool call made by the model."""

    tool_name: str
    arguments: dict[str, Any]
    result: str = ""


class ConversationTurn(BaseModel):
    """One turn in the conversation (assistant response + tool calls)."""

    assistant_text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class ExecutionTrace(BaseModel):
    """Complete trace of a task execution for evaluation."""

    task_id: str
    provider_name: str
    model_name: str
    activation_mode: ActivationMode
    artifacts_dir: str = ""
    raw_messages: list[dict[str, Any]] = Field(default_factory=list)
    turns: list[ConversationTurn] = Field(default_factory=list)
    final_output: str = ""
    activated_skills: list[str] = Field(default_factory=list)
    bash_commands: list[str] = Field(default_factory=list)
    files_read: list[str] = Field(default_factory=list)
    files_written: list[str] = Field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    error: str | None = None

    def record_tool_call(self, call: ToolCall) -> None:
        if call.tool_name == "bash":
            self.bash_commands.append(call.arguments.get("command", ""))
        elif call.tool_name == "read_file":
            path = call.arguments.get("path", "")
            self.files_read.append(path)
            if path.endswith("SKILL.md"):
                skill_dir = Path(path).parent.name
                if skill_dir not in self.activated_skills:
                    self.activated_skills.append(skill_dir)
        elif call.tool_name == "write_file":
            self.files_written.append(call.arguments.get("path", ""))


class OracleResult(BaseModel):
    """Result of evaluating a task execution with an oracle function."""

    task_score: float = Field(ge=0.0, le=1.0)
    skill_selection_score: float = Field(ge=0.0, le=1.0, default=0.0)
    instruction_following_score: float = Field(ge=0.0, le=1.0, default=0.0)
    details: dict[str, Any] = Field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        return (self.task_score + self.skill_selection_score + self.instruction_following_score) / 3


class TaskResult(BaseModel):
    """Final result for one task + one model combination."""

    task_id: str
    task_name: str
    task_query: str = ""
    category: str
    provider_name: str
    model_name: str
    activation_mode: ActivationMode
    oracle_result: OracleResult
    trace: ExecutionTrace
    error: str | None = None


class EvalReport(BaseModel):
    """Aggregated evaluation report across tasks and models."""

    results: list[TaskResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class SamplingParams(BaseModel):
    """Optional model hyperparameters. None means 'don't send, use API default'."""

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider (proxy).

    A provider is an API endpoint that can serve multiple models.
    """

    provider_type: str
    api_key_env: str
    models: list[str] = Field(default_factory=list)
    base_url: str | None = None
    sampling: SamplingParams = SamplingParams()


class EvalConfig(BaseModel):
    """Top-level evaluation configuration."""

    skills_dir: str = "skills"
    tasks_dir: str = "tasks"
    activation_mode: ActivationMode = ActivationMode.CATALOG
    max_turns: int = 10
    bash_timeout: int = 30
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
