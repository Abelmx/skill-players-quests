"""Oracle for USD/JPY exchange rate query task."""
import subprocess
import json
import re
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection, check_bash_patterns

def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    # Get reference rate from frankfurter.app
    ref_rate = None
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.frankfurter.app/latest?from=USD&to=JPY"],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        ref_rate = data["rates"]["JPY"]
    except Exception:
        pass

    # Extract numbers from output that could be exchange rates (typically 100-200 for USD/JPY)
    numbers = re.findall(r"\d+\.?\d*", output)
    task_ok = False
    if ref_rate is not None and numbers:
        for n in numbers:
            try:
                val = float(n)
                if 50 < val < 500 and abs(val - ref_rate) / ref_rate <= 0.01:
                    task_ok = True
                    break
            except ValueError:
                continue
    elif numbers:
        for n in numbers:
            try:
                val = float(n)
                if 50 < val < 500:
                    task_ok = True
                    break
            except ValueError:
                continue

    skill_score = check_skill_selection(trace, ["exchange-rate"])
    instr_score = check_bash_patterns(trace, ["frankfurter|get_rate"])

    return OracleResult(
        task_score=1.0 if task_ok else 0.0,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={"ref_rate": ref_rate, "model_output_excerpt": output[:200]},
    )
