"""Oracle for WCAG accessible login form task."""
import re
from pathlib import Path
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    html_path = Path("login.html")
    if not html_path.exists():
        for p in trace.files_written:
            if p.endswith("login.html"):
                html_path = Path(p)
                break

    if not html_path.exists():
        return OracleResult(
            task_score=0.0,
            skill_selection_score=check_skill_selection(trace, ["frontend-design"]),
            instruction_following_score=0.0,
            details={"error": "login.html not found"},
        )

    html = html_path.read_text(encoding="utf-8")

    checks = {}

    # 1. Input elements have associated labels (for= or aria-label or aria-labelledby)
    inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
    labeled_inputs = 0
    for inp in inputs:
        input_id = re.search(r'id=["\']([^"\']+)', inp)
        has_aria = bool(re.search(r'aria-label|aria-labelledby', inp))
        has_label_for = False
        if input_id:
            has_label_for = bool(re.search(
                rf'<label[^>]*for=["\']' + re.escape(input_id.group(1)),
                html, re.IGNORECASE
            ))
        if has_aria or has_label_for:
            labeled_inputs += 1
    checks["inputs_labeled"] = labeled_inputs >= 2 if inputs else False

    # 2. Has role attributes
    checks["has_role"] = bool(re.search(r'role=', html, re.IGNORECASE))

    # 3. Button has explicit text (not empty)
    buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.IGNORECASE | re.DOTALL)
    checks["button_text"] = any(btn.strip() for btn in buttons) if buttons else False

    # 4. Has aria-required on required fields
    checks["aria_required"] = bool(re.search(r'aria-required|required', html, re.IGNORECASE))

    # 5. Has focus styles
    checks["focus_styles"] = bool(re.search(r':focus|:focus-visible|:focus-within', html))

    passed = sum(1 for v in checks.values() if v)
    task_score = passed / len(checks)

    skill_score = check_skill_selection(trace, ["frontend-design"])
    read_design_ref = any("design-system" in f or "frontend-design" in f for f in trace.files_read)
    instr_score = 1.0 if read_design_ref else 0.5

    return OracleResult(
        task_score=task_score,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details=checks,
    )
