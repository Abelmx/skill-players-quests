"""Oracle for webpage screenshot task."""
from pathlib import Path
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import (
    check_file_exists,
    check_file_is_valid_image,
    check_skill_selection,
    check_bash_patterns,
)


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    file_exists = check_file_exists("screenshot.png")
    valid_image = check_file_is_valid_image("screenshot.png") if file_exists else False

    # Check file size (should be >1KB for a real screenshot)
    reasonable_size = False
    if file_exists:
        size = Path("screenshot.png").stat().st_size
        reasonable_size = size > 1024

    task_score = 1.0 if (file_exists and valid_image and reasonable_size) else (
        0.5 if file_exists else 0.0
    )

    skill_score = check_skill_selection(trace, ["web-screenshot"])
    instr_score = check_bash_patterns(trace, ["screenshot|playwright"])

    return OracleResult(
        task_score=task_score,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={
            "file_exists": file_exists,
            "valid_image": valid_image,
            "reasonable_size": reasonable_size,
        },
    )
