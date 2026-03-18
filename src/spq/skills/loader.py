"""SKILL.md parser and loader following the AgentSkills specification."""

from __future__ import annotations

import logging
from pathlib import Path

import frontmatter

from spq.core.models import SkillMeta

logger = logging.getLogger(__name__)


def parse_skill_md(path: Path) -> SkillMeta | None:
    """Parse a single SKILL.md file into SkillMeta.

    Handles malformed YAML leniently per the agentskills.io client implementation guide.
    """
    try:
        post = frontmatter.load(str(path))
    except Exception:
        try:
            text = path.read_text(encoding="utf-8")
            lines = text.split("\n")
            if lines[0].strip() == "---":
                end = -1
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == "---":
                        end = i
                        break
                if end > 0:
                    fm_text = "\n".join(lines[1:end])
                    import yaml

                    fm_data = yaml.safe_load(fm_text) or {}
                    body = "\n".join(lines[end + 1 :]).strip()
                    post = frontmatter.Post(body, **fm_data)
                else:
                    logger.warning("Could not find closing --- in %s, skipping", path)
                    return None
            else:
                logger.warning("No frontmatter found in %s, skipping", path)
                return None
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            return None

    name = post.get("name", "")
    description = post.get("description", "")

    if not description:
        logger.warning("Skill at %s has no description, skipping", path)
        return None

    if not name:
        name = path.parent.name
        logger.warning("Skill at %s has no name, using directory name '%s'", path, name)

    if len(name) > 64:
        logger.warning("Skill name '%s' exceeds 64 chars", name)

    if name != path.parent.name:
        logger.warning(
            "Skill name '%s' doesn't match parent directory '%s'", name, path.parent.name
        )

    return SkillMeta(
        name=name,
        description=description,
        location=path.resolve(),
        base_dir=path.parent.resolve(),
        license=post.get("license"),
        compatibility=post.get("compatibility"),
        metadata=post.get("metadata") or {},
        body=post.content,
    )


def discover_skills(skills_dir: Path) -> list[SkillMeta]:
    """Scan a directory tree for SKILL.md files and parse them."""
    skills: list[SkillMeta] = []
    if not skills_dir.exists():
        logger.warning("Skills directory does not exist: %s", skills_dir)
        return skills

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        if any(part.startswith(".") for part in skill_md.parts):
            continue
        meta = parse_skill_md(skill_md)
        if meta:
            skills.append(meta)
            logger.debug("Discovered skill: %s at %s", meta.name, meta.location)

    return skills
