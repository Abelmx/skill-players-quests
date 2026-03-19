# Skill-Players-Quests

[简体中文](README.zh-CN.md)

Skill-Players-Quests is a framework for evaluating how `(m)LLM` general agents use [Agent Skills](https://agentskills.io/what-are-skills) in realistic task settings.

It is designed for agents that do not start with a large set of built-in specialized tools. Instead, the model is asked to discover relevant skills, load the right `SKILL.md`, follow its instructions, and complete the task end to end. The current repository is an evolving MVP, so the framework, task set, and benchmark coverage will continue to change.

## What This Framework Is

This framework evaluates an agent's ability to use skills as an external capability layer:

- choose the right skill from a candidate pool
- activate the skill by reading its `SKILL.md`
- follow skill-specific instructions, scripts, and references
- complete the downstream task with real execution and oracle-based scoring

The focus is not generic tool calling in the abstract. The focus is whether a general agent can successfully work with the skill protocol that is already widely used in practice.

## Features

- Multi-provider, multi-model evaluation with parallel execution.
- Two skill injection strategies:
  - progressive injection via `catalog` mode, where the agent sees a skill catalog first and reads full skill content on demand
  - aggressive injection via `full_inject` mode, where all selected skill content is injected up front
- Per-task oracle evaluation for:
  - `skill_selection_score`
  - `instruction_following_score`
  - `task_score`
- Local runs for fast iteration and GitHub Actions runs for a cleaner sandboxed environment.
- Structured outputs including per-task results, message traces, model reports, and cross-model comparison reports.

## Quick Start

### Local

Set up the full evaluation environment first. This installs not only the framework itself, but also the dependencies required by bundled skills.

```bash
bash setup.sh
# or: bash setup.sh 3.12
```

`setup.sh` will:

- create `.venv`
- install framework dependencies and bundled skill dependencies
- install Playwright Chromium for screenshot-related skills
- check required system tools such as `curl`, `dig`, `gh`, `jq`, and `tar`

Then configure the framework and environment variables.

First, review `configs/default.yaml`. This file defines:

- which providers are available
- which models belong to each provider
- which environment variable each provider uses for its API key via `api_key_env`
- default runtime settings such as `activation_mode`, `max_turns`, and `bash_timeout`

Example:

```yaml
providers:
  boyue:
    api_key_env: "SPQ_API_KEY"
    base_url: "http://..."
    models:
      - "gpt-5.4"
```

Then create your local `.env` from the template and fill in the required keys `SPQ_API_KEY`:

```bash
cp .env.example .env
# edit .env and set the keys referenced by configs/default.yaml
source activate.sh
```

In practice:

- if `configs/default.yaml` uses `api_key_env: "SPQ_API_KEY"`, then set `SPQ_API_KEY` in `.env`
- if it uses `api_key_env: "GUIJI_API_KEY"`, then set `GUIJI_API_KEY`
- if a task depends on extra skill credentials, also set those, for example `IMAGE_GEN_API_KEY` or `GITHUB_TOKEN`

Environment variables take precedence over `configs/default.yaml`, so you can keep stable defaults in config and override them per machine or per run.

Useful commands:

```bash
python3 -m spq show-config
python3 -m spq list-skills
python3 -m spq list-tasks
```

Run one model on all tasks:

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m catalog
```

Run selected tasks only:

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m catalog \
  -t tokyo-weather \
  -t usd-jpy-rate
```

Run with aggressive injection:

```bash
python3 -m spq run -p boyue --model gpt-5.4 -m full_inject
```

Run multiple providers/models and let the framework write outputs under `results/`:

```bash
python3 -m spq run -p boyue -p guiji -m catalog -j 2
```

### GitHub Actions Sandbox

For safer and cleaner evaluation, you can run the same benchmark in GitHub Actions inside a containerized environment.

Before running the workflow:

1. Create a dedicated evaluation branch (e.g. `eval/quiz-1`) and configure the models you want to evaluate in `configs/default.yaml` on that branch.
2. Push the branch to GitHub.
3. Set repository secrets such as `SPQ_API_KEY`, `GUIJI_API_KEY`, `INTERN_API_KEY`, and any skill-specific secrets (e.g. image generation credentials).

Then:

1. Open the `SPQ Evaluation` workflow in GitHub Actions.
2. Optionally specify task IDs, concurrency, and injection mode.
3. Run the workflow.
4. Review the generated reports and artifacts in the PR automatically created by the workflow, then merge the results back into your evaluation branch.

## Recommended Workflow

For reproducible evaluations, we recommend using a dedicated evaluation branch rather than running directly on `main`.

Suggested flow:

1. Create an evaluation branch and freeze the framework version, task set, and config there.
2. Run evaluations locally or through GitHub Actions.
3. Commit the generated `results/` back to that evaluation branch.
4. Compare runs without mixing benchmark changes into `main`.

This keeps benchmark evolution and benchmark results separate. A more detailed workflow guide will be documented separately.

## Current MVP Coverage

Current bundled coverage in this repository:

- `10` tasks
- `15` skills
- `5` task categories

### Task Categories


| Category              | Example tasks                                     |
| --------------------- | ------------------------------------------------- |
| `realtime-data`       | `tokyo-weather`, `usd-jpy-rate`                   |
| `external-api`        | `generate-qr-code`, `generate-cyberpunk-image`    |
| `service-interaction` | `react-bug-issues`, `npm-express-version`         |
| `design-standards`    | `accessible-login-form`, `brutalist-product-page` |
| `specialized-tools`   | `domain-dns-lookup`, `webpage-screenshot`         |


### Included Skills

Representative bundled skills include:

- `weather`
- `exchange-rate`
- `github`
- `package-registry`
- `dns-lookup`
- `web-screenshot`
- `qr-code`
- `image-gen`
- `frontend-design`
- `code-formatter`
- `calculator`

The current MVP mostly focuses on single-skill task execution with distractor skills included in each task's candidate pool.

## Evaluation Results (Sanity Check)

We ran an initial sanity-check evaluation to validate the framework and methodology. Results from this run are available on the [`eval/quiz-1`](https://github.com/Abelmx/skill-players-quests/tree/eval/quiz-1/results) branch.

This evaluation is intended to verify the feasibility of the approach -- whether the task design, skill injection, oracle scoring, and end-to-end pipeline work as expected. The current 10 tasks are relatively simple (single-skill, "EASY" mode) and primarily serve as a baseline for iterating on both the framework and the models under test. Task coverage, difficulty, and complexity will continue to expand.

> **Disclaimer**: LLM outputs are non-deterministic. Results are for reference and model optimization only, and should not be interpreted as a subjective judgement of any model by the skill-players-quests project.

## Results

Each evaluation run writes structured outputs under `results/`:

- `results.jsonl`: one record per task result
- `traces.jsonl`: raw conversation and tool trace per task
- `report.json`: aggregated metrics for one model run
- `report.md`: human-readable per-model report
- `eval_*-models.md`: cross-model comparison report when multiple models are evaluated together

This makes it easy to inspect both final scores and the actual activation/execution path taken by the agent.

## Scoring

Each task has its own oracle function. Oracles can inspect final text output, files written to the task artifact directory, and execution traces.

The main scoring dimensions are:


| Metric                        | Meaning                                                  |
| ----------------------------- | -------------------------------------------------------- |
| `task_score`                  | whether the task was actually completed                  |
| `skill_selection_score`       | whether the agent activated the expected skill           |
| `instruction_following_score` | whether the agent followed the skill's intended workflow |


## Repository Layout

```text
skill-players-quests/
├── configs/              # framework configuration
├── skills/               # bundled skills pool
├── tasks/                # evaluation tasks and task-specific oracles
├── src/spq/core/         # config and data models
├── src/spq/skills/       # skill discovery and registry
├── src/spq/providers/    # model provider adapters
├── src/spq/runtime/      # prompt building, conversation loop, tool execution
├── src/spq/evaluation/   # oracle helpers, metrics, reporting
└── .github/workflows/    # sandboxed CI evaluation workflow
```

## Notes

- This repository is currently an MVP and will continue to evolve.
- Task definitions, skill pool composition, oracle logic, and reporting format may still change.
- If you want stable comparisons, pin the exact branch or commit used for evaluation.

