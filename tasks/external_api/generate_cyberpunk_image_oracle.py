"""Oracle for cyberpunk image generation task."""
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_file_exists, check_file_is_valid_image, check_skill_selection, check_bash_patterns


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    file_exists = check_file_exists("output.png", trace)
    valid_image = check_file_is_valid_image("output.png", trace) if file_exists else False

    task_score = 1.0 if (file_exists and valid_image) else (0.5 if file_exists else 0.0)

    return OracleResult(
        task_score=task_score,
        skill_selection_score=check_skill_selection(trace, ["image-gen"]),
        instruction_following_score=check_bash_patterns(trace, ["generate_image"]),
        details={"file_exists": file_exists, "valid_image": valid_image},
    )
