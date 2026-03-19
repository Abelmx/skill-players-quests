"""Oracle for npm express version query task."""
import subprocess
import json
import re
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection, check_bash_patterns


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    # Get reference version from npm registry
    ref_version = None
    try:
        result = subprocess.run(
            ["curl", "-s", "https://registry.npmjs.org/express/latest"],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        ref_version = data.get("version")
    except Exception:
        pass

    task_ok = False
    if ref_version and ref_version in output:
        task_ok = True
    elif ref_version:
        # Check if major.minor matches
        parts = ref_version.split(".")
        if len(parts) >= 2:
            partial = f"{parts[0]}.{parts[1]}"
            task_ok = partial in output

    skill_score = check_skill_selection(trace, ["package-registry"])
    instr_score = check_bash_patterns(trace, ["registry\\.npmjs|query_registry"])

    return OracleResult(
        task_score=1.0 if task_ok else 0.0,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={"ref_version": ref_version, "model_output_excerpt": output[:200]},
    )
