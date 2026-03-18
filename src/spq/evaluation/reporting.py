"""Report generation — terminal tables, JSON output, and comparison matrices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from spq.core.models import TaskResult
from spq.evaluation.metrics import (
    compute_efficiency,
    compute_instruction_following_rate,
    compute_pass_rate,
    compute_skill_selection_accuracy,
)
from spq.evaluation.scorer import aggregate_by_category, aggregate_by_model


def build_summary(results: list[TaskResult]) -> dict[str, Any]:
    """Build the full evaluation summary."""
    return {
        "total_tasks": len(results),
        "by_model": aggregate_by_model(results),
        "by_category": aggregate_by_category(results),
        "global_pass_rate": compute_pass_rate(results),
        "global_skill_selection": compute_skill_selection_accuracy(results),
        "global_instruction_following": compute_instruction_following_rate(results),
        "global_efficiency": compute_efficiency(results),
    }


def _task_result_to_dict(r: TaskResult) -> dict[str, Any]:
    """Serialize a single TaskResult to a dict suitable for JSON output."""
    return {
        "task_id": r.task_id,
        "task_name": r.task_name,
        "category": r.category,
        "provider": r.provider_name,
        "model": r.model_name,
        "activation_mode": r.activation_mode.value,
        "scores": {
            "task_score": r.oracle_result.task_score,
            "skill_selection_score": r.oracle_result.skill_selection_score,
            "instruction_following_score": r.oracle_result.instruction_following_score,
            "overall_score": r.oracle_result.overall_score,
        },
        "details": r.oracle_result.details,
        "turns": len(r.trace.turns),
        "tokens": {
            "input": r.trace.total_input_tokens,
            "output": r.trace.total_output_tokens,
        },
        "activated_skills": r.trace.activated_skills,
        "bash_commands": r.trace.bash_commands,
        "files_written": r.trace.files_written,
        "error": r.error,
    }


def append_task_result(jsonl_path: Path, result: TaskResult) -> None:
    """Append a single TaskResult as one JSON line to a .jsonl file."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "a", encoding="utf-8") as f:
        line = json.dumps(_task_result_to_dict(result), ensure_ascii=False, default=str)
        f.write(line + "\n")


def save_summary_report(report_path: Path, results: list[TaskResult]) -> None:
    """Write the aggregate summary report.json (no per-task details)."""
    summary = build_summary(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)


def print_model_summary(results: list[TaskResult], console: Console | None = None) -> None:
    """Print a per-model summary table to the terminal."""
    console = console or Console()
    by_model = aggregate_by_model(results)

    table = Table(title="Model Evaluation Summary", show_lines=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Task Score", justify="right")
    table.add_column("Skill Select", justify="right")
    table.add_column("Instr Follow", justify="right")
    table.add_column("Overall", justify="right", style="bold")
    table.add_column("Pass/Total", justify="right")

    for model, scores in sorted(by_model.items()):
        table.add_row(
            model,
            f"{scores['task_score']:.2f}",
            f"{scores['skill_selection_score']:.2f}",
            f"{scores['instruction_following_score']:.2f}",
            f"{scores['overall_score']:.2f}",
            f"{scores['tasks_passed']}/{scores['total_tasks']}",
        )

    console.print(table)


def print_task_details(results: list[TaskResult], console: Console | None = None) -> None:
    """Print per-task detail table."""
    console = console or Console()

    table = Table(title="Task Detail Results", show_lines=True)
    table.add_column("Task", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Task", justify="right")
    table.add_column("Skill", justify="right")
    table.add_column("Instr", justify="right")
    table.add_column("Turns", justify="right")
    table.add_column("Error", max_width=30)

    for r in results:
        table.add_row(
            r.task_id,
            f"{r.provider_name}/{r.model_name}",
            f"{r.oracle_result.task_score:.2f}",
            f"{r.oracle_result.skill_selection_score:.2f}",
            f"{r.oracle_result.instruction_following_score:.2f}",
            str(len(r.trace.turns)),
            r.error or "",
        )

    console.print(table)


def print_category_matrix(results: list[TaskResult], console: Console | None = None) -> None:
    """Print a category x model comparison matrix."""
    console = console or Console()
    by_cat = aggregate_by_category(results)

    models = sorted({f"{r.provider_name}/{r.model_name}" for r in results})

    table = Table(title="Category × Model Matrix", show_lines=True)
    table.add_column("Category", style="cyan")
    for m in models:
        table.add_column(m, justify="right")

    for category in sorted(by_cat.keys()):
        row = [category]
        for m in models:
            scores = by_cat[category].get(m, {})
            overall = scores.get("overall_score", 0.0)
            row.append(f"{overall:.2f}")
        table.add_row(*row)

    console.print(table)


def load_results_jsonl(jsonl_path: Path) -> list[dict[str, Any]]:
    """Load all task result dicts from a results.jsonl file."""
    results: list[dict[str, Any]] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def save_model_report_md(path: Path, results: list[TaskResult]) -> None:
    """Generate a human-readable Markdown report for a single model's results."""
    if not results:
        return
    from datetime import datetime

    r0 = results[0]
    model_key = f"{r0.provider_name}/{r0.model_name}"
    by_model = aggregate_by_model(results)
    scores = by_model.get(model_key, {})

    total_in = sum(r.trace.total_input_tokens for r in results)
    total_out = sum(r.trace.total_output_tokens for r in results)

    lines: list[str] = []
    lines.append(f"# Evaluation Report: {model_key}\n")
    lines.append(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Mode**: {r0.activation_mode.value}")
    lines.append(f"- **Tasks**: {len(results)}")
    lines.append(f"- **Tokens**: {total_in:,} input / {total_out:,} output\n")

    # Model Summary
    lines.append("## Summary\n")
    lines.append("| Metric | Score |")
    lines.append("|--------|------:|")
    lines.append(f"| Task Score | {scores.get('task_score', 0):.2f} |")
    lines.append(f"| Skill Selection | {scores.get('skill_selection_score', 0):.2f} |")
    lines.append(f"| Instruction Following | {scores.get('instruction_following_score', 0):.2f} |")
    lines.append(f"| **Overall** | **{scores.get('overall_score', 0):.2f}** |")
    lines.append(f"| Pass / Total | {scores.get('tasks_passed', 0)} / {scores.get('total_tasks', 0)} |")
    lines.append("")

    # Task Details
    lines.append("## Task Details\n")
    lines.append("| Task | Category | Task Score | Skill | Instr | Turns | Error |")
    lines.append("|------|----------|----------:|------:|------:|------:|-------|")
    for r in results:
        o = r.oracle_result
        err = r.error or ""
        if len(err) > 40:
            err = err[:37] + "..."
        lines.append(
            f"| {r.task_id} | {r.category} | {o.task_score:.2f} | "
            f"{o.skill_selection_score:.2f} | {o.instruction_following_score:.2f} | "
            f"{len(r.trace.turns)} | {err} |"
        )
    lines.append("")

    # Activated Skills
    lines.append("## Activated Skills\n")
    lines.append("| Task | Skills Used |")
    lines.append("|------|------------|")
    for r in results:
        skills = ", ".join(r.trace.activated_skills) if r.trace.activated_skills else "-"
        lines.append(f"| {r.task_id} | {skills} |")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_comparison_report_md(path: Path, all_results: list[TaskResult]) -> None:
    """Generate a cross-model comparison Markdown report."""
    if not all_results:
        return
    from datetime import datetime

    by_model = aggregate_by_model(all_results)
    by_cat = aggregate_by_category(all_results)
    models = sorted(by_model.keys())
    task_ids = sorted({r.task_id for r in all_results})

    lines: list[str] = []
    lines.append("# Multi-Model Evaluation Comparison\n")
    lines.append(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Models**: {len(models)}")
    lines.append(f"- **Tasks**: {len(task_ids)}\n")

    for m in models:
        lines.append(f"  - `{m}`")
    lines.append("")

    # Model Summary comparison
    lines.append("## Model Summary\n")
    lines.append("| Model | Task Score | Skill Select | Instr Follow | Overall | Pass/Total |")
    lines.append("|-------|----------:|------------:|------------:|--------:|----------:|")
    for m in models:
        s = by_model[m]
        lines.append(
            f"| {m} | {s['task_score']:.2f} | {s['skill_selection_score']:.2f} | "
            f"{s['instruction_following_score']:.2f} | **{s['overall_score']:.2f}** | "
            f"{s['tasks_passed']}/{s['total_tasks']} |"
        )
    lines.append("")

    # Category x Model Matrix
    categories = sorted(by_cat.keys())
    lines.append("## Category × Model Matrix\n")
    header = "| Category | " + " | ".join(models) + " |"
    sep = "|----------|" + "|".join("------:" for _ in models) + "|"
    lines.append(header)
    lines.append(sep)
    for cat in categories:
        row = f"| {cat}"
        for m in models:
            sc = by_cat[cat].get(m, {})
            row += f" | {sc.get('overall_score', 0):.2f}"
        row += " |"
        lines.append(row)
    lines.append("")

    # Per-task comparison
    lines.append("## Per-Task Comparison\n")
    header = "| Task | " + " | ".join(models) + " |"
    sep = "|------|" + "|".join("------:" for _ in models) + "|"
    lines.append(header)
    lines.append(sep)

    results_by_task_model: dict[str, dict[str, TaskResult]] = {}
    for r in all_results:
        key = f"{r.provider_name}/{r.model_name}"
        results_by_task_model.setdefault(r.task_id, {})[key] = r

    for tid in task_ids:
        row = f"| {tid}"
        for m in models:
            r = results_by_task_model.get(tid, {}).get(m)
            if r:
                score = r.oracle_result.overall_score
                mark = "PASS" if r.oracle_result.task_score >= 1.0 else "FAIL"
                row += f" | {score:.2f} ({mark})"
            else:
                row += " | - "
        row += " |"
        lines.append(row)
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def save_json_report(results: list[TaskResult], output_path: Path) -> None:
    """Save full results and summary as a single JSON (legacy compatibility)."""
    summary = build_summary(results)

    report = {
        "summary": summary,
        "results": [_task_result_to_dict(r) for r in results],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
