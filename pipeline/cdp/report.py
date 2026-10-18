"""cdp report — bảng + biểu đồ: dự báo vs đo, Pareto chu kỳ–LUT, roofline.

CHƯA HIỆN THỰC. Dự kiến ở bước S8: xuất report/pipeline/ từ sổ cái
"""
from __future__ import annotations

STEP = "S8"
WHAT = "xuất report/pipeline/ từ sổ cái"


def main(args, run) -> int:
    run.say(f"cdp report: chưa hiện thực — dự kiến ở S8")
    run.say(f"    xuất report/pipeline/ từ sổ cái")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
