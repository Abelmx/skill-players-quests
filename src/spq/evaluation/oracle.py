"""Oracle function framework and base utilities."""

from __future__ import annotations

import re

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


def check_file_exists(path: str) -> bool:
    """Check if a file exists at the given path."""
    from pathlib import Path

    return Path(path).exists()


def check_file_is_valid_image(path: str) -> bool:
    """Check if a file is a valid image using basic header checks."""
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return False

    data = p.read_bytes()
    if len(data) < 8:
        return False

    # PNG magic bytes
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # JPEG magic bytes
    if data[:2] == b"\xff\xd8":
        return True
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return True
    # WebP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True

    return False
