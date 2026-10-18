"""cdp sim — chạy Verilator qua Makefile có sẵn, đọc chu kỳ từng lớp và CRC.

CHƯA HIỆN THỰC. Dự kiến ở bước S1: bọc make sim-v* / sim-bv*, phân tích các dòng M1S,cyc và M1S,crc
"""
from __future__ import annotations

STEP = "S1"
WHAT = "bọc make sim-v* / sim-bv*, phân tích các dòng M1S,cyc và M1S,crc"


def main(args, run) -> int:
    run.say(f"cdp sim: chưa hiện thực — dự kiến ở S1")
    run.say(f"    bọc make sim-v* / sim-bv*, phân tích các dòng M1S,cyc và M1S,crc")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
