"""Score aggregation across tasks and models."""

from __future__ import annotations

from collections import defaultdict

from spq.core.models import TaskResult


def aggregate_by_model(results: list[TaskResult]) -> dict[str, dict[str, float]]:
    """Aggregate scores by model, returning per-model averages."""
    model_scores: dict[str, list[TaskResult]] = defaultdict(list)
    for r in results:
        key = f"{r.provider_name}/{r.model_name}"
        model_scores[key].append(r)

    summary = {}
    for model_key, model_results in model_scores.items():
        n = len(model_results)
        summary[model_key] = {
            "task_score": sum(r.oracle_result.task_score for r in model_results) / n,
            "skill_selection_score": sum(
                r.oracle_result.skill_selection_score for r in model_results
            ) / n,
            "instruction_following_score": sum(
                r.oracle_result.instruction_following_score for r in model_results
            ) / n,
            "overall_score": sum(r.oracle_result.overall_score for r in model_results) / n,
            "total_tasks": n,
            "tasks_passed": sum(1 for r in model_results if r.oracle_result.task_score >= 0.5),
        }
    return summary


def aggregate_by_category(results: list[TaskResult]) -> dict[str, dict[str, dict[str, float]]]:
    """Aggregate scores by category x model."""
    cat_model: dict[str, dict[str, list[TaskResult]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        model_key = f"{r.provider_name}/{r.model_name}"
        cat_model[r.category][model_key].append(r)

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for category, models in cat_model.items():
        summary[category] = {}
        for model_key, model_results in models.items():
            n = len(model_results)
            summary[category][model_key] = {
                "task_score": sum(r.oracle_result.task_score for r in model_results) / n,
                "overall_score": sum(r.oracle_result.overall_score for r in model_results) / n,
                "count": n,
            }
    return summary
