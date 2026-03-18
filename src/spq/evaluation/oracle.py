"""Oracle function framework and base utilities."""

from __future__ import annotations

import re
from pathlib import Path

from spq.core.models import ExecutionTrace, OracleResult


def check_skill_selection(trace: ExecutionTrace, expected_skills: list[str]) -> float:
    """Score skill selection: 1.0 if all expected skills were activated and no extras."""
    if not expected_skills:
        return 1.0

    activated = set(trace.activated_skills)
    expected = set(expected_skills)

    if not activated:
        return 0.0

    correct = activated & expected
    score = len(correct) / len(expected)
    return score


def check_bash_patterns(trace: ExecutionTrace, patterns: list[str]) -> float:
    """Score instruction following by checking if bash commands match expected patterns."""
    if not patterns:
        return 1.0

    matched = 0
    for pattern in patterns:
        for cmd in trace.bash_commands:
            if re.search(pattern, cmd):
                matched += 1
                break

    return matched / len(patterns)


def _resolve_artifact(filename: str, trace: ExecutionTrace) -> Path | None:
    """Resolve a filename inside the task's artifacts directory."""
    if not trace.artifacts_dir:
        return None
    p = Path(trace.artifacts_dir) / filename
    return p if p.exists() else None


def check_file_exists(filename: str, trace: ExecutionTrace) -> bool:
    """Check if an output file exists in the task's artifacts directory."""
    return _resolve_artifact(filename, trace) is not None


def check_file_is_valid_image(filename: str, trace: ExecutionTrace) -> bool:
    """Check if a file in the artifacts directory is a valid image."""
    p = _resolve_artifact(filename, trace)
    if p is None:
        return False

    data = p.read_bytes()
    if len(data) < 8:
        return False

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:2] == b"\xff\xd8":
        return True
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True

    return False


def check_file_size(filename: str, trace: ExecutionTrace, min_bytes: int = 0) -> bool:
    """Check if a file in the artifacts directory meets a minimum size."""
    p = _resolve_artifact(filename, trace)
    if p is None:
        return False
    return p.stat().st_size > min_bytes
