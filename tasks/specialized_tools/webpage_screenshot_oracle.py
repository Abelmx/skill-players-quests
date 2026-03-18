"""Oracle for webpage screenshot task."""
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import (
    check_file_exists,
    check_file_is_valid_image,
    check_file_size,
    check_skill_selection,
    check_bash_patterns,
)


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    file_exists = check_file_exists("screenshot.png", trace)
    valid_image = check_file_is_valid_image("screenshot.png", trace) if file_exists else False
    reasonable_size = check_file_size("screenshot.png", trace, min_bytes=1024)

    task_score = 1.0 if (file_exists and valid_image and reasonable_size) else (
        0.5 if file_exists else 0.0
    )

    return OracleResult(
        task_score=task_score,
        skill_selection_score=check_skill_selection(trace, ["web-screenshot"]),
        instruction_following_score=check_bash_patterns(trace, ["screenshot|playwright"]),
        details={
            "file_exists": file_exists,
            "valid_image": valid_image,
            "reasonable_size": reasonable_size,
        },
    )
