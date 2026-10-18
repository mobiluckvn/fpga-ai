"""cdp verify — cổng kiểm chứng cho ứng viên đã hiện thực.

CHƯA HIỆN THỰC. Dự kiến ở bước S6: kiểm ngẫu nhiên vs plugin ISS, riscv-tests 48/48, đúng bit M1-S, ISS=Verilator, SRC_HASH
"""
from __future__ import annotations

STEP = "S6"
WHAT = "kiểm ngẫu nhiên vs plugin ISS, riscv-tests 48/48, đúng bit M1-S, ISS=Verilator, SRC_HASH"


def main(args, run) -> int:
    run.say(f"cdp verify: chưa hiện thực — dự kiến ở S6")
    run.say(f"    kiểm ngẫu nhiên vs plugin ISS, riscv-tests 48/48, đúng bit M1-S, ISS=Verilator, SRC_HASH")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
