---
name: github
description: Query GitHub repositories, issues, pull requests, and CI status using the gh CLI. Use when the user asks about GitHub repos, issues, PRs, or code.
---

# GitHub Query

## Instructions

When the user asks about GitHub repositories, issues, pull requests, or code:

### Common gh CLI commands

```bash
# Repo info
gh repo view OWNER/REPO

# List issues (optionally filter by label)
gh issue list -R OWNER/REPO --limit 20
gh issue list -R OWNER/REPO -l bug

# List pull requests
gh pr list -R OWNER/REPO --limit 20

# CI status
gh run list -R OWNER/REPO
```

### Run the script

```bash
./scripts/gh_query.sh OWNER/REPO [resource_type] [label]
```

- `resource_type`: `issues` (default), `prs`, `runs`
- `label`: optional filter for issues/PRs

Output is in JSON format.

## Usage Examples

```bash
# List issues (default)
./scripts/gh_query.sh owner/repo

# List issues with label
./scripts/gh_query.sh owner/repo issues bug

# List PRs
./scripts/gh_query.sh owner/repo prs

# CI runs
./scripts/gh_query.sh owner/repo runs
```

## Notes

- Requires `gh` CLI to be installed and authenticated (`gh auth login`).
