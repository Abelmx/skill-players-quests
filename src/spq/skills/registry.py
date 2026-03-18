"""Skill registry for managing discovered skills."""

from __future__ import annotations

import logging
from pathlib import Path

from spq.core.models import SkillMeta
from spq.skills.loader import discover_skills

logger = logging.getLogger(__name__)


class SkillRegistry:
    """In-memory registry of all available skills, keyed by name."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillMeta] = {}

    def load_from_directory(self, skills_dir: Path) -> None:
        for skill in discover_skills(skills_dir):
            if skill.name in self._skills:
                logger.warning(
                    "Skill name collision: '%s' at %s shadows %s",
                    skill.name,
                    skill.location,
                    self._skills[skill.name].location,
                )
            self._skills[skill.name] = skill

    def get(self, name: str) -> SkillMeta | None:
        return self._skills.get(name)

    def get_many(self, names: list[str]) -> list[SkillMeta]:
        result = []
        for name in names:
            skill = self._skills.get(name)
            if skill:
                result.append(skill)
            else:
                logger.warning("Skill '%s' not found in registry", name)
        return result

    def list_all(self) -> list[SkillMeta]:
        return list(self._skills.values())

    @property
    def count(self) -> int:
        return len(self._skills)

    def build_catalog_xml(self, skill_names: list[str]) -> str:
        """Build an XML catalog string for Mode A (progressive disclosure).

        Only includes name, description, and location for each skill.
        """
        skills = self.get_many(skill_names)
        if not skills:
            return ""

        lines = [
            "<available_skills>",
            "The following skills provide specialized instructions for specific tasks.",
            "When a task matches a skill's description, use your read_file tool to load",
            "the SKILL.md at the listed location before proceeding.",
            "When a skill references relative paths, resolve them against the skill's",
            "directory (the parent of SKILL.md) and use absolute paths in tool calls.",
            "",
        ]
        for s in skills:
            lines.append("<skill>")
            lines.append(f"  <name>{s.name}</name>")
            lines.append(f"  <description>{s.description}</description>")
            lines.append(f"  <location>{s.location}</location>")
            lines.append("</skill>")
        lines.append("</available_skills>")
        return "\n".join(lines)

    def build_full_inject_xml(self, skill_names: list[str]) -> str:
        """Build full-inject XML for Mode B (all skill content in system prompt).

        Each skill block includes directory path and resource listing.
        """
        skills = self.get_many(skill_names)
        if not skills:
            return ""

        blocks = []
        for s in skills:
            resources = self._list_resources(s.base_dir)
            resource_xml = ""
            if resources:
                resource_lines = ["\n<skill_resources>"]
                for r in resources:
                    resource_lines.append(f"  <file>{r}</file>")
                resource_lines.append("</skill_resources>")
                resource_xml = "\n".join(resource_lines)

            block = (
                f'<skill_content name="{s.name}">\n'
                f"{s.body}\n\n"
                f"Skill directory: {s.base_dir}\n"
                f"Relative paths in this skill are relative to the skill directory."
                f"{resource_xml}\n"
                f"</skill_content>"
            )
            blocks.append(block)
        return "\n\n".join(blocks)

    @staticmethod
    def _list_resources(base_dir: Path) -> list[str]:
        """List scripts/, references/, and assets/ files relative to base_dir."""
        resources = []
        for subdir in ("scripts", "references", "assets"):
            d = base_dir / subdir
            if d.exists():
                for f in sorted(d.rglob("*")):
                    if f.is_file():
                        resources.append(str(f.relative_to(base_dir)))
        return resources
