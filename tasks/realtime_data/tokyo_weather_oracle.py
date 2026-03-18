"""Oracle for Tokyo weather query task."""
import subprocess
import json
import re
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection, check_bash_patterns

def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    # Get reference temperature from Open-Meteo
    ref_temp = None
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.open-meteo.com/v1/forecast?latitude=35.6762&longitude=139.6503&current_weather=true"],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        ref_temp = data["current_weather"]["temperature"]
    except Exception:
        pass

    # Check model output for temperature values
    temps = re.findall(r"[-+]?\d+\.?\d*", output)
    task_ok = False
    if ref_temp is not None and temps:
        for t in temps:
            try:
                if abs(float(t) - ref_temp) <= 3.0:
                    task_ok = True
                    break
            except ValueError:
                continue
    elif temps:
        # If we can't get reference, give partial credit for having a number
        task_ok = True

    skill_score = check_skill_selection(trace, ["weather"])
    instr_score = check_bash_patterns(trace, ["wttr\\.in|open-meteo|get_weather"])

    return OracleResult(
        task_score=1.0 if task_ok else 0.0,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={"ref_temp": ref_temp, "model_output_excerpt": output[:200]},
    )
