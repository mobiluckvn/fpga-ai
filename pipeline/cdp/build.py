"""cdp build — build firmware (cờ) + RTL (tham số) bằng Makefile có sẵn.

CHƯA HIỆN THỰC. Dự kiến ở bước S1: bọc make -C experiment/m1s fw-v* và make -C rtl/mycore build-bv* (có FAST_ADDR/WITH_DOT4/WITH_REQ), dựng ngoài cây để không sửa thư mục build đã commit
"""
from __future__ import annotations

STEP = "S1"
WHAT = "bọc make -C experiment/m1s fw-v* và make -C rtl/mycore build-bv* (có FAST_ADDR/WITH_DOT4/WITH_REQ), dựng ngoài cây để không sửa thư mục build đã commit"


def main(args, run) -> int:
    run.say(f"cdp build: chưa hiện thực — dự kiến ở S1")
    run.say(f"    bọc make -C experiment/m1s fw-v* và make -C rtl/mycore build-bv* (có FAST_ADDR/WITH_DOT4/WITH_REQ), dựng ngoài cây để không sửa thư mục build đã commit")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
