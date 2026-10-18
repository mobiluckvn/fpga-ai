"""cdp profile — profile 3 tầng từ trace của ISS.

CHƯA HIỆN THỰC. Dự kiến ở bước S3: hàm/lớp · khối cơ bản/vòng lặp · mẫu lệnh, theo SPEC 2.2
"""
from __future__ import annotations

STEP = "S3"
WHAT = "hàm/lớp · khối cơ bản/vòng lặp · mẫu lệnh, theo SPEC 2.2"


def main(args, run) -> int:
    run.say(f"cdp profile: chưa hiện thực — dự kiến ở S3")
    run.say(f"    hàm/lớp · khối cơ bản/vòng lặp · mẫu lệnh, theo SPEC 2.2")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
