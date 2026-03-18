"""Skill activation logic for both modes (catalog / full-inject)."""

from __future__ import annotations

from spq.core.models import ActivationMode, TaskDef
from spq.skills.registry import SkillRegistry


SYSTEM_PROMPT_BASE = """\
You are an AI assistant with access to tools (read_file, bash, write_file).
You can use these tools to accomplish the user's task.
Complete the task and provide your final answer as text.
"""

ARTIFACTS_INSTRUCTION = """\
<output_directory>
All output files (images, documents, generated code, etc.) MUST be saved to:
  {artifacts_dir}
Use absolute paths when writing files. Example: {artifacts_dir}/output.png
Do NOT write output files to any other location.
</output_directory>"""


def build_system_prompt(
    registry: SkillRegistry,
    task: TaskDef,
    mode: ActivationMode,
    artifacts_dir: str = "",
) -> str:
    """Build the system prompt based on activation mode."""
    parts = [SYSTEM_PROMPT_BASE.strip()]

    if artifacts_dir:
        parts.append(ARTIFACTS_INSTRUCTION.format(artifacts_dir=artifacts_dir))

    if mode == ActivationMode.CATALOG:
        catalog = registry.build_catalog_xml(task.available_skills)
        if catalog:
            parts.append(catalog)
    elif mode == ActivationMode.FULL_INJECT:
        inject = registry.build_full_inject_xml(task.available_skills)
        if inject:
            parts.append(inject)

    return "\n\n".join(parts)
