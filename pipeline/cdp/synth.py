"""cdp synth — tổng hợp để lấy chi phí (LUT/DFF/MULT) và Fmax.

CHƯA HIỆN THỰC. Dự kiến ở bước S1: bọc yosys/nextpnr của hai Makefile + scripts/pnr_report.py
"""
from __future__ import annotations

STEP = "S1"
WHAT = "bọc yosys/nextpnr của hai Makefile + scripts/pnr_report.py"


def main(args, run) -> int:
    run.say(f"cdp synth: chưa hiện thực — dự kiến ở S1")
    run.say(f"    bọc yosys/nextpnr của hai Makefile + scripts/pnr_report.py")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
