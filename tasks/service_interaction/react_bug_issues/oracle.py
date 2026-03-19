"""Oracle for React DevTools issues query task."""
import subprocess
import json
import re
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection, check_bash_patterns

def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    # Get reference issues from gh CLI
    ref_issues = []
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", "facebook/react",
             "--label", "Component: Developer Tools",
             "--state", "open", "--limit", "3", "--json", "number,title"],
            capture_output=True, text=True, timeout=30,
        )
        ref_issues = json.loads(result.stdout)
    except Exception:
        pass

    # Check if model output contains issue numbers
    task_ok = False
    if ref_issues:
        found = 0
        for issue in ref_issues:
            if str(issue["number"]) in output:
                found += 1
        task_ok = found >= 2  # At least 2 of 3 issues found
    else:
        # If we can't get reference, check model at least has issue numbers
        issue_numbers = re.findall(r"#?\d{4,6}", output)
        task_ok = len(issue_numbers) >= 2

    skill_score = check_skill_selection(trace, ["github"])
    instr_score = check_bash_patterns(trace, ["gh.*issue|gh_query"])

    return OracleResult(
        task_score=1.0 if task_ok else 0.0,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={
            "ref_issues": ref_issues,
            "model_output_excerpt": output[:300],
        },
    )
