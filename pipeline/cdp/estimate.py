"""cdp estimate — dự báo cho từng ứng viên (giải tích + ISS).

CHƯA HIỆN THỰC. Dự kiến ở bước S6: ghi dự báo vào sổ cái TRƯỚC khi hiện thực (SPEC 0.3)
"""
from __future__ import annotations

STEP = "S6"
WHAT = "ghi dự báo vào sổ cái TRƯỚC khi hiện thực (SPEC 0.3)"


def main(args, run) -> int:
    run.say(f"cdp estimate: chưa hiện thực — dự kiến ở S6")
    run.say(f"    ghi dự báo vào sổ cái TRƯỚC khi hiện thực (SPEC 0.3)")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
