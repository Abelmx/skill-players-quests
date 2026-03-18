"""Oracle for brutalist product page task."""
import re
from pathlib import Path
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection

FORBIDDEN_FONTS = ["Inter", "Arial", "Roboto", "Helvetica"]


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    html_path = Path("index.html")
    if not html_path.exists():
        # Check if written via write_file tool
        for p in trace.files_written:
            if p.endswith("index.html"):
                html_path = Path(p)
                break

    if not html_path.exists():
        return OracleResult(
            task_score=0.0,
            skill_selection_score=check_skill_selection(trace, ["frontend-design"]),
            instruction_following_score=0.0,
            details={"error": "index.html not found"},
        )

    html = html_path.read_text(encoding="utf-8")

    checks = {}

    # 1. No forbidden fonts as sole font
    has_forbidden = False
    for font in FORBIDDEN_FONTS:
        # Check for font-family declarations using only forbidden fonts
        pattern = rf"font-family\s*:\s*['\"]?{font}['\"]?\s*[;}}]"
        if re.search(pattern, html, re.IGNORECASE):
            has_forbidden = True
    checks["no_forbidden_fonts"] = not has_forbidden

    # 2. Uses CSS custom properties (variables)
    checks["css_variables"] = bool(re.search(r"--[\w-]+\s*:", html))

    # 3. Has animation/transition properties
    checks["has_animations"] = bool(re.search(r"animation|transition|@keyframes", html, re.IGNORECASE))

    # 4. Imports Google Fonts
    checks["google_fonts"] = bool(re.search(r"fonts\.googleapis\.com|fonts\.gstatic\.com", html))

    # 5. Not a single centered card layout (heuristic: check for non-trivial layout)
    checks["not_centered_card"] = not bool(re.search(
        r"margin\s*:\s*\d+px\s+auto.*max-width\s*:\s*\d+px",
        html, re.DOTALL
    )) or bool(re.search(r"grid|flex.*wrap|columns|float", html, re.IGNORECASE))

    passed = sum(1 for v in checks.values() if v)
    task_score = passed / len(checks)

    skill_score = check_skill_selection(trace, ["frontend-design"])

    # Check if model read the design-system reference
    read_design_ref = any("design-system" in f for f in trace.files_read)
    instr_score = 1.0 if read_design_ref else 0.5

    return OracleResult(
        task_score=task_score,
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details=checks,
    )
