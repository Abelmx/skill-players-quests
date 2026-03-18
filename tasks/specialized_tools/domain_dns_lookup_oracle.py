"""Oracle for DNS lookup task."""
import subprocess
import re
from spq.core.models import ExecutionTrace, OracleResult
from spq.evaluation.oracle import check_skill_selection, check_bash_patterns


def evaluate(output: str, trace: ExecutionTrace) -> OracleResult:
    # Get reference A records
    ref_ips = []
    try:
        result = subprocess.run(
            ["dig", "+short", "openai.com", "A"],
            capture_output=True, text=True, timeout=10,
        )
        ref_ips = [ip.strip() for ip in result.stdout.strip().split("\n") if ip.strip()]
    except Exception:
        pass

    # Get reference MX records
    ref_mx = []
    try:
        result = subprocess.run(
            ["dig", "+short", "openai.com", "MX"],
            capture_output=True, text=True, timeout=10,
        )
        ref_mx = [mx.strip() for mx in result.stdout.strip().split("\n") if mx.strip()]
    except Exception:
        pass

    # Check model output
    has_ip = bool(re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', output))
    has_mx = bool(re.search(r'mail|mx|smtp', output, re.IGNORECASE)) or bool(
        re.search(r'\d+\s+\S+\.\S+\.', output)
    )

    # Verify at least one IP matches
    ip_match = False
    if ref_ips:
        for ip in ref_ips:
            if ip in output:
                ip_match = True
                break

    task_ok = has_ip and has_mx
    if ref_ips and not ip_match:
        task_ok = False  # IPs don't match reference

    skill_score = check_skill_selection(trace, ["dns-lookup"])
    instr_score = check_bash_patterns(trace, ["dig|nslookup|lookup"])

    return OracleResult(
        task_score=1.0 if task_ok else (0.5 if has_ip or has_mx else 0.0),
        skill_selection_score=skill_score,
        instruction_following_score=instr_score,
        details={
            "ref_ips": ref_ips,
            "ref_mx": ref_mx,
            "has_ip": has_ip,
            "has_mx": has_mx,
        },
    )
