"""Metrics computation utilities."""

from __future__ import annotations

from spq.core.models import TaskResult


def compute_pass_rate(results: list[TaskResult], threshold: float = 0.5) -> float:
    """Compute the fraction of tasks that pass (task_score >= threshold)."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.oracle_result.task_score >= threshold)
    return passed / len(results)


def compute_skill_selection_accuracy(results: list[TaskResult]) -> float:
    """Average skill selection score across all results."""
    if not results:
        return 0.0
    return sum(r.oracle_result.skill_selection_score for r in results) / len(results)


def compute_instruction_following_rate(results: list[TaskResult]) -> float:
    """Average instruction following score across all results."""
    if not results:
        return 0.0
    return sum(r.oracle_result.instruction_following_score for r in results) / len(results)


def compute_efficiency(results: list[TaskResult]) -> dict[str, float]:
    """Compute average token usage."""
    if not results:
        return {"avg_input_tokens": 0, "avg_output_tokens": 0, "avg_turns": 0}

    n = len(results)
    return {
        "avg_input_tokens": sum(r.trace.total_input_tokens for r in results) / n,
        "avg_output_tokens": sum(r.trace.total_output_tokens for r in results) / n,
        "avg_turns": sum(len(r.trace.turns) for r in results) / n,
    }
