"""Task execution orchestrator — ties everything together."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

import yaml

from spq.core.models import (
    ActivationMode,
    EvalConfig,
    OracleResult,
    TaskDef,
    TaskResult,
)
from spq.providers.base import LLMProvider
from spq.runtime.activator import build_system_prompt
from spq.runtime.conversation import ConversationManager
from spq.runtime.executor import ToolExecutor
from spq.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


def load_tasks(tasks_dir: Path) -> list[TaskDef]:
    """Discover and load all task YAML definitions."""
    tasks: list[TaskDef] = []
    if not tasks_dir.exists():
        return tasks
    for yaml_file in sorted(tasks_dir.rglob("task.yaml")):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data and "id" in data:
                tasks.append(TaskDef(**data))
        except Exception as e:
            logger.error("Failed to load task %s: %s", yaml_file, e)
    return tasks


def load_oracle(module_path: str, project_root: Path | None = None):
    """Dynamically load an oracle module and return its evaluate function.

    If project_root is given, temporarily add it to sys.path so that
    oracle modules under tasks/ can be imported by dotted path.
    """
    import sys

    added = False
    if project_root and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        added = True
    try:
        mod = importlib.import_module(module_path)
    finally:
        if added:
            sys.path.remove(str(project_root))

    if not hasattr(mod, "evaluate"):
        raise AttributeError(f"Oracle module {module_path} has no 'evaluate' function")
    return mod.evaluate


class Orchestrator:
    """Runs evaluation tasks against LLM providers."""

    def __init__(
        self,
        config: EvalConfig,
        registry: SkillRegistry,
        project_root: Path | None = None,
    ) -> None:
        self.config = config
        self.registry = registry
        self.project_root = project_root

    async def run_task(
        self,
        task: TaskDef,
        provider: LLMProvider,
        mode: ActivationMode | None = None,
        artifacts_dir: str = "",
    ) -> TaskResult:
        mode = mode or self.config.activation_mode

        system_prompt = build_system_prompt(
            self.registry, task, mode, artifacts_dir=artifacts_dir,
        )
        executor = ToolExecutor(timeout=self.config.bash_timeout)
        conv = ConversationManager(provider, executor, max_turns=self.config.max_turns)

        logger.info(
            "Running task '%s' with %s/%s in %s mode",
            task.id, provider.name, provider.model, mode.value,
        )

        trace = await conv.run(system_prompt, task, mode)
        trace.artifacts_dir = artifacts_dir

        oracle_result = self._evaluate(task, trace)

        return TaskResult(
            task_id=task.id,
            task_name=task.name,
            task_query=task.query,
            category=task.category,
            provider_name=provider.name,
            model_name=provider.model,
            activation_mode=mode,
            oracle_result=oracle_result,
            trace=trace,
            error=trace.error,
        )

    def _evaluate(self, task: TaskDef, trace) -> OracleResult:
        oracle_module = task.oracle.get("module", "")
        if not oracle_module:
            logger.warning("Task %s has no oracle module, scoring zero", task.id)
            return OracleResult(task_score=0.0)

        try:
            evaluate_fn = load_oracle(oracle_module, self.project_root)
            return evaluate_fn(trace.final_output, trace)
        except Exception as e:
            logger.error("Oracle evaluation failed for %s: %s", task.id, e)
            return OracleResult(
                task_score=0.0,
                details={"oracle_error": str(e)},
            )

    async def run_all(
        self,
        tasks: list[TaskDef],
        providers: list[LLMProvider],
        mode: ActivationMode | None = None,
    ) -> list[TaskResult]:
        results: list[TaskResult] = []
        for provider in providers:
            for task in tasks:
                result = await self.run_task(task, provider, mode)
                results.append(result)
                logger.info(
                    "  %s | %s | task=%.2f skill=%.2f instr=%.2f",
                    task.id,
                    provider.name,
                    result.oracle_result.task_score,
                    result.oracle_result.skill_selection_score,
                    result.oracle_result.instruction_following_score,
                )
        return results
