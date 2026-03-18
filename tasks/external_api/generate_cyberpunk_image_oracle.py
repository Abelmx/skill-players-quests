"""Oracle for cyberpunk image generation task."""
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_file_exists, check_file_is_valid_image, check_skill_selection, check_bash_patterns

def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    file_exists = check_file_exists("output.png")
    valid_image = check_file_is_valid_image("output.png") if file_exists else False

    task_score = 1.0 if (file_exists and valid_image) else (0.5 if file_exists else 0.0)
    skill_score = check_skill_selection(trace, ["image-gen"])
    instr_score = check_bash_patterns(trace, ["generate_image"])

    return OracleResult(
        task_score=task_score,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={
            "file_exists": file_exists,
            "valid_image": valid_image,
        },
    )
