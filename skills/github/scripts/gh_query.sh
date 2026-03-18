#!/usr/bin/env bash
# Query GitHub repo via gh CLI

REPO="${1:-}"
RESOURCE="${2:-issues}"
LABEL="${3:-}"

if [[ -z "$REPO" ]]; then
  echo "Usage: $0 REPO [resource_type] [label]"
  echo "  resource_type: issues (default), prs, runs"
  echo "  label: optional filter for issues/PRs"
  exit 1
fi

case "$RESOURCE" in
  issues)
    if [[ -n "$LABEL" ]]; then
      gh issue list -R "$REPO" -l "$LABEL" --limit 50 --json number,title,state,labels,createdAt
    else
      gh issue list -R "$REPO" --limit 50 --json number,title,state,labels,createdAt
    fi
    ;;
  prs)
    if [[ -n "$LABEL" ]]; then
      gh pr list -R "$REPO" -l "$LABEL" --limit 50 --json number,title,state,createdAt
    else
      gh pr list -R "$REPO" --limit 50 --json number,title,state,createdAt
    fi
    ;;
  runs)
    gh run list -R "$REPO" --limit 20 --json databaseId,displayTitle,status,conclusion,createdAt
    ;;
  *)
    echo "Unknown resource: $RESOURCE (use issues, prs, or runs)"
    exit 1
    ;;
esac
