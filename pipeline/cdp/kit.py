"""cdp kit — nạp + đo trên kit qua script có sẵn, có khoá kit và đối chứng.

CHƯA HIỆN THỰC. Dự kiến ở bước S1: bọc make load-* + check-* và scripts/m1s_check.py, qua kitlock, đối chứng min/top.fs như scripts/branch_b_measure.sh
"""
from __future__ import annotations

STEP = "S1"
WHAT = "bọc make load-* + check-* và scripts/m1s_check.py, qua kitlock, đối chứng min/top.fs như scripts/branch_b_measure.sh"


def main(args, run) -> int:
    run.say(f"cdp kit: chưa hiện thực — dự kiến ở S1")
    run.say(f"    bọc make load-* + check-* và scripts/m1s_check.py, qua kitlock, đối chứng min/top.fs như scripts/branch_b_measure.sh")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
