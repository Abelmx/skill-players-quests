"""Skill activation logic for both modes (catalog / full-inject)."""

from __future__ import annotations

from spq.core.models import ActivationMode, TaskDef
from spq.skills.registry import SkillRegistry


SYSTEM_PROMPT_BASE = """\
You are an AI assistant with access to tools (read_file, bash, write_file).
You can use these tools to accomplish the user's task.
Complete the task and provide your final answer as text.
"""


def build_system_prompt(
    registry: SkillRegistry,
    task: TaskDef,
    mode: ActivationMode,
) -> str:
    """Build the system prompt based on activation mode."""
    parts = [SYSTEM_PROMPT_BASE.strip()]

    if mode == ActivationMode.CATALOG:
        catalog = registry.build_catalog_xml(task.available_skills)
        if catalog:
            parts.append(catalog)
    elif mode == ActivationMode.FULL_INJECT:
        inject = registry.build_full_inject_xml(task.available_skills)
        if inject:
            parts.append(inject)

    return "\n\n".join(parts)
