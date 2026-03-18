"""CLI entry point for the evaluation framework."""

from __future__ import annotations

import asyncio
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table

from spq.core.config import load_config
from spq.core.models import ActivationMode, ProviderConfig, TaskResult
from spq.evaluation.reporting import (
    append_task_result,
    load_results_jsonl,
    print_category_matrix,
    print_model_summary,
    print_task_details,
    save_comparison_report_md,
    save_model_report_md,
    save_summary_report,
)
from spq.providers.base import LLMProvider
from spq.providers.openai_provider import OpenAIProvider
from spq.runtime.orchestrator import Orchestrator, load_tasks
from spq.skills.registry import SkillRegistry

console = Console()
logger = logging.getLogger("spq")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _resolve_project_root() -> Path:
    """Walk up from CWD to find pyproject.toml or tasks/ directory."""
    cwd = Path.cwd()
    for p in [cwd, *cwd.parents]:
        if (p / "pyproject.toml").exists() and (p / "tasks").exists():
            return p
    return cwd


def _create_provider(
    provider_name: str,
    model: str,
    cfg: ProviderConfig,
) -> LLMProvider:
    """Create an OpenAI-compatible provider for one specific model."""
    return OpenAIProvider(
        model=model,
        api_key_env=cfg.api_key_env,
        base_url=cfg.base_url,
        provider_name=provider_name,
        sampling=cfg.sampling,
    )


def _build_run_dir(base: Path, provider_name: str, model: str) -> Path:
    """Create output directory: results/{provider_model}/{YYYYMMDD-HHmmss}/"""
    model_slug = f"{provider_name}_{model}".replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = base / model_slug / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "artifacts").mkdir(exist_ok=True)
    return run_dir


def _collect_artifacts(trace: Any, task_id: str, artifacts_dir: Path) -> int:
    """Copy files written during task execution into artifacts/{task_id}/."""
    collected = 0
    if not trace.files_written:
        return collected
    dest_dir = artifacts_dir / task_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    for filepath in trace.files_written:
        src = Path(filepath)
        if src.exists() and src.is_file():
            try:
                shutil.copy2(src, dest_dir / src.name)
                collected += 1
            except OSError:
                pass
    return collected


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds) // 60
    secs = seconds - minutes * 60
    return f"{minutes}m {secs:.0f}s"


# ── Progress tracking for parallel runs ──────────────────────────────────────

class ModelProgress:
    """Thread-safe progress state for one model evaluation."""

    def __init__(self, provider_name: str, model: str, total_tasks: int) -> None:
        self.provider_name = provider_name
        self.model = model
        self.total = total_tasks
        self.done = 0
        self.passed = 0
        self.failed = 0
        self.current_task = ""
        self.finished = False


def _build_progress_table(
    trackers: list[ModelProgress],
    elapsed: float,
) -> Table:
    """Build a Rich table showing real-time progress for all models."""
    table = Table(title="Evaluation Progress", show_lines=False)
    table.add_column("Model", style="cyan", no_wrap=True, min_width=30)
    table.add_column("Progress", justify="right", min_width=10)
    table.add_column("Pass", justify="right", style="green", min_width=5)
    table.add_column("Fail", justify="right", style="red", min_width=5)
    table.add_column("Current Task", style="dim", min_width=25)

    for t in trackers:
        status = "done" if t.finished else t.current_task
        table.add_row(
            f"{t.provider_name}/{t.model}",
            f"{t.done}/{t.total}",
            str(t.passed),
            str(t.failed),
            status,
        )

    table.caption = f"Elapsed: {_format_duration(elapsed)}"
    return table


# ── Core run logic ───────────────────────────────────────────────────────────

async def _run_model_tasks(
    orchestrator: Orchestrator,
    provider: LLMProvider,
    tasks: list,
    mode: ActivationMode,
    run_dir: Path,
    semaphore: asyncio.Semaphore,
    progress: ModelProgress,
    serial_log: bool = False,
) -> list[TaskResult]:
    """Run all tasks for a single model, respecting concurrency semaphore."""
    jsonl_path = run_dir / "results.jsonl"
    artifacts_dir = run_dir / "artifacts"
    results: list[TaskResult] = []

    async def _run_one(task):
        async with semaphore:
            progress.current_task = task.id
            result = await orchestrator.run_task(task, provider, mode)
            append_task_result(jsonl_path, result)
            _collect_artifacts(result.trace, task.id, artifacts_dir)

            progress.done += 1
            if result.oracle_result.task_score >= 1.0:
                progress.passed += 1
            else:
                progress.failed += 1

            if serial_log:
                o = result.oracle_result
                status = "[green]PASS[/green]" if o.task_score >= 1.0 else "[red]FAIL[/red]"
                console.print(
                    f"  [{progress.done}/{progress.total}]  "
                    f"{result.task_id:<30s}  {status}  "
                    f"task={o.task_score:.2f} skill={o.skill_selection_score:.2f} "
                    f"instr={o.instruction_following_score:.2f}  "
                    f"({len(result.trace.turns)} turns)"
                )

            return result

    gathered = await asyncio.gather(*[_run_one(t) for t in tasks])
    results.extend(gathered)
    progress.current_task = ""
    progress.finished = True

    report_path = run_dir / "report.json"
    save_summary_report(report_path, results)
    save_model_report_md(run_dir / "report.md", results)
    return results


async def _run_all_models(
    orchestrator: Orchestrator,
    model_specs: list[tuple[str, str, ProviderConfig]],
    tasks: list,
    mode: ActivationMode,
    results_base: Path,
    concurrency: int,
) -> list[TaskResult]:
    """Run evaluation across all models in parallel."""
    trackers: list[ModelProgress] = []
    coros = []
    is_parallel = len(model_specs) > 1 or concurrency > 1

    for provider_name, model_id, pcfg in model_specs:
        provider = _create_provider(provider_name, model_id, pcfg)
        run_dir = _build_run_dir(results_base, provider_name, model_id)
        progress = ModelProgress(provider_name, model_id, len(tasks))
        trackers.append(progress)

        console.print(f"  {provider_name}/{model_id} → {run_dir}")

        sem = asyncio.Semaphore(concurrency)
        coros.append(_run_model_tasks(
            orchestrator, provider, tasks, mode, run_dir, sem, progress,
            serial_log=not is_parallel,
        ))
    all_results: list[TaskResult] = []
    start = time.time()

    if is_parallel:
        with Live(
            _build_progress_table(trackers, 0),
            console=console,
            refresh_per_second=2,
        ) as live:
            async def _refresh_loop():
                while not all(t.finished for t in trackers):
                    live.update(_build_progress_table(trackers, time.time() - start))
                    await asyncio.sleep(0.5)
                live.update(_build_progress_table(trackers, time.time() - start))

            refresh_task = asyncio.create_task(_refresh_loop())
            gathered = await asyncio.gather(*coros)
            for r in gathered:
                all_results.extend(r)
            await refresh_task
    else:
        for i, coro in enumerate(coros):
            tracker = trackers[i]
            results = await coro
            all_results.extend(results)

    elapsed = time.time() - start
    console.print(f"\nAll tasks completed in {_format_duration(elapsed)}\n")
    return all_results


# ── CLI commands ─────────────────────────────────────────────────────────────

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """Skill-Players-Quests: LLM Skills evaluation framework."""
    _setup_logging(verbose)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
@click.option("--provider", "-p", multiple=True, help="Provider names to evaluate")
@click.option("--model", multiple=True, help="Specific model IDs to evaluate")
@click.option(
    "--mode", "-m",
    type=click.Choice(["catalog", "full_inject"]),
    default=None,
    help="Skill activation mode",
)
@click.option("--task", "-t", multiple=True, help="Specific task IDs to run")
@click.option(
    "--concurrency", "-j", type=int, default=1,
    help="Number of tasks to run in parallel per model (default: 1)",
)
@click.option(
    "--output", "-o", type=click.Path(), default=None,
    help="Base output directory (default: results/)",
)
def run(
    config: str | None,
    provider: tuple[str, ...],
    model: tuple[str, ...],
    mode: str | None,
    task: tuple[str, ...],
    concurrency: int,
    output: str | None,
) -> None:
    """Run evaluation tasks against LLM providers."""
    project_root = _resolve_project_root()
    cfg = load_config(Path(config) if config else project_root / "configs" / "default.yaml")

    registry = SkillRegistry()
    skills_dir = project_root / cfg.skills_dir
    registry.load_from_directory(skills_dir)
    console.print(f"Loaded {registry.count} skills from {skills_dir}")

    tasks_dir = project_root / cfg.tasks_dir
    all_tasks = load_tasks(tasks_dir)
    if task:
        all_tasks = [t for t in all_tasks if t.id in task]
    console.print(f"Found {len(all_tasks)} tasks")

    if not all_tasks:
        console.print("[red]No tasks found![/red]")
        sys.exit(1)

    # Build (provider_name, model_id, provider_config) list
    provider_names = list(provider) if provider else list(cfg.providers.keys())
    model_specs: list[tuple[str, str, ProviderConfig]] = []
    for pname in provider_names:
        if pname not in cfg.providers:
            console.print(f"[red]Provider '{pname}' not found in config[/red]")
            sys.exit(1)
        pcfg = cfg.providers[pname]
        for mid in pcfg.models:
            if model and mid not in model:
                continue
            model_specs.append((pname, mid, pcfg))

    if not model_specs:
        console.print("[red]No models to evaluate! Check --provider / --model flags.[/red]")
        sys.exit(1)

    activation_mode = ActivationMode(mode) if mode else cfg.activation_mode

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    orchestrator = Orchestrator(cfg, registry, project_root=project_root)
    results_base = Path(output) if output else project_root / "results"

    console.print(
        f"\nRunning {len(all_tasks)} tasks × {len(model_specs)} models "
        f"in {activation_mode.value} mode (concurrency={concurrency})\n"
    )
    console.print("[bold]输出目录:[/bold]")

    all_results = asyncio.run(_run_all_models(
        orchestrator, model_specs, all_tasks, activation_mode,
        results_base, concurrency,
    ))

    print_model_summary(all_results, console)
    print_task_details(all_results, console)
    print_category_matrix(all_results, console)

    if len(model_specs) > 1:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        comparison_path = results_base / f"eval_{timestamp}_{len(model_specs)}-models.md"
        save_comparison_report_md(comparison_path, all_results)
        console.print(f"\n[bold]Comparison report[/bold] → {comparison_path}")


@cli.command("show-config")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
def show_config(config: str | None) -> None:
    """Display current evaluation configuration (providers, models, env status)."""
    import os

    project_root = _resolve_project_root()
    cfg = load_config(Path(config) if config else project_root / "configs" / "default.yaml")

    console.print("\n[bold]Framework Settings[/bold]")
    settings = Table(show_header=False, box=None, padding=(0, 2))
    settings.add_column("Key", style="dim")
    settings.add_column("Value")
    settings.add_row("activation_mode", cfg.activation_mode.value)
    settings.add_row("max_turns", str(cfg.max_turns))
    settings.add_row("bash_timeout", f"{cfg.bash_timeout}s")
    settings.add_row("skills_dir", cfg.skills_dir)
    settings.add_row("tasks_dir", cfg.tasks_dir)
    console.print(settings)

    console.print("\n[bold]Providers & Models[/bold]")
    pt = Table(show_lines=True)
    pt.add_column("Provider", style="cyan")
    pt.add_column("Base URL", style="dim", max_width=50)
    pt.add_column("API Key Env", style="yellow")
    pt.add_column("Key Status")
    pt.add_column("Models", style="green")

    total_models = 0
    for name, pcfg in cfg.providers.items():
        key_val = os.environ.get(pcfg.api_key_env)
        if key_val:
            key_status = "[green]set[/green]"
        else:
            key_status = "[red]not set[/red]"
        models_str = "\n".join(pcfg.models) if pcfg.models else "[dim]none[/dim]"
        total_models += len(pcfg.models)
        pt.add_row(name, pcfg.base_url or "-", pcfg.api_key_env, key_status, models_str)

    console.print(pt)
    console.print(f"\n  {len(cfg.providers)} provider(s), {total_models} model(s) total\n")


@cli.command("list-tasks")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
def list_tasks(config: str | None) -> None:
    """List all available evaluation tasks."""
    project_root = _resolve_project_root()
    cfg = load_config(Path(config) if config else project_root / "configs" / "default.yaml")

    tasks = load_tasks(project_root / cfg.tasks_dir)
    console.print(f"\nFound {len(tasks)} tasks:\n")

    t = Table(show_lines=True)
    t.add_column("ID", style="cyan")
    t.add_column("Name")
    t.add_column("Category", style="green")
    t.add_column("Difficulty")
    t.add_column("Expected Skills", style="yellow")

    for task in tasks:
        t.add_row(
            task.id, task.name, task.category, task.difficulty,
            ", ".join(task.expected_skills),
        )
    console.print(t)


@cli.command("list-skills")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
def list_skills(config: str | None) -> None:
    """List all available skills in the pool."""
    project_root = _resolve_project_root()
    cfg = load_config(Path(config) if config else project_root / "configs" / "default.yaml")

    registry = SkillRegistry()
    registry.load_from_directory(project_root / cfg.skills_dir)

    t = Table(title="Skills Pool", show_lines=True)
    t.add_column("Name", style="cyan")
    t.add_column("Description", max_width=60)
    t.add_column("Location", style="dim", max_width=50)

    for skill in registry.list_all():
        t.add_row(skill.name, skill.description, str(skill.base_dir))
    console.print(t)


@cli.command()
@click.argument("report_path", type=click.Path(exists=True))
def report(report_path: str) -> None:
    """Display a previously saved evaluation report.

    Accepts either:
      - A directory containing report.json + results.jsonl (new format)
      - A single .json file (legacy format)
      - A .jsonl file (results only, no summary)
    """
    from spq.core.models import (
        ActivationMode,
        ConversationTurn,
        ExecutionTrace,
        OracleResult,
        TaskResult,
    )

    p = Path(report_path)
    raw_results: list[dict] = []

    if p.is_dir():
        jsonl = p / "results.jsonl"
        if jsonl.exists():
            raw_results = load_results_jsonl(jsonl)
        else:
            console.print(f"[red]No results.jsonl found in {p}[/red]")
            sys.exit(1)
    elif p.suffix == ".jsonl":
        raw_results = load_results_jsonl(p)
    else:
        import json
        with open(p) as f:
            data = json.load(f)
        raw_results = data.get("results", [])

    if not raw_results:
        console.print("[red]No results found.[/red]")
        sys.exit(1)

    results: list[TaskResult] = []
    for r in raw_results:
        trace = ExecutionTrace(
            task_id=r["task_id"],
            provider_name=r["provider"],
            model_name=r["model"],
            activation_mode=ActivationMode(r["activation_mode"]),
            activated_skills=r.get("activated_skills", []),
            bash_commands=r.get("bash_commands", []),
            files_written=r.get("files_written", []),
            total_input_tokens=r.get("tokens", {}).get("input", 0),
            total_output_tokens=r.get("tokens", {}).get("output", 0),
        )
        for _ in range(r.get("turns", 0)):
            trace.turns.append(ConversationTurn())

        results.append(TaskResult(
            task_id=r["task_id"],
            task_name=r.get("task_name", r["task_id"]),
            category=r["category"],
            provider_name=r["provider"],
            model_name=r["model"],
            activation_mode=ActivationMode(r["activation_mode"]),
            oracle_result=OracleResult(**r["scores"], details=r.get("details", {})),
            trace=trace,
            error=r.get("error"),
        ))

    print_model_summary(results, console)
    print_task_details(results, console)
    print_category_matrix(results, console)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
