"""cdp analyze — ILP (đường găng), DLP, byte/MAC, roofline.

CHƯA HIỆN THỰC. Dự kiến ở bước S3: sinh analysis.json từ profile.json
"""
from __future__ import annotations

STEP = "S3"
WHAT = "sinh analysis.json từ profile.json"


def main(args, run) -> int:
    run.say(f"cdp analyze: chưa hiện thực — dự kiến ở S3")
    run.say(f"    sinh analysis.json từ profile.json")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
