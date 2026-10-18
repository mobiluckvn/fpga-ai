"""Dựng hạ tầng firmware cho S6: gốc là ĐÚNG B-V3, kernel thay được.

Khác `prepare.py` (dùng cho S4) ở chỗ giải chỉ thị tiền xử lý với bốn macro tính năng
**ĐANG BẬT** (OPT_KERNELS, USE_DOT4, CONV1_DOT4, USE_REQ), tức bản firmware nhanh nhất
hiện có. Nhờ vậy ứng viên phần cứng mới được thử **trên đỉnh** B-V3, không phải trên mã
C thẳng.

Cổng kiểm bắt buộc: firmware dựng từ `kernels_v3.c` phải cho đúng 365.992 chu kỳ, bằng
tuyệt đối từng lớp từng ảnh như B-V3.
"""
from __future__ import annotations

from pathlib import Path

from .. import paths
from .prepare import FEATURES, REGION_END, REGION_START, resolve, split

ON = frozenset({"OPT_KERNELS", "USE_DOT4", "CONV1_DOT4", "USE_REQ"})
OUT_DIR = paths.ROOT / "experiment" / "m1s_s6"
SRC = paths.M1S / "main.c"


def main_prepare(say=print) -> dict:
    lines = SRC.read_text().splitlines(keepends=True)
    # Cắt ranh giới trên file GỐC (mốc cuối `#ifdef REQ_BENCH` là một chỉ thị tính năng,
    # giải trước thì mốc biến mất), rồi mới giải từng phần với bốn macro bật.
    rest_raw, kern_raw = split(lines)
    kern = resolve(kern_raw, ON)
    rest = resolve(rest_raw, ON)
    kept = rest + kern
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "main.c").write_text("".join(rest))
    (OUT_DIR / "kernels_v3.c").write_text("".join(kern))
    leaked = [f for f in FEATURES if f in "".join(kern)]
    say(f"    main.c {len(lines)} dòng -> giải với {sorted(ON)} còn {len(kept)} dòng")
    say(f"    experiment/m1s_s6/main.c       : {len(rest)} dòng")
    say(f"    experiment/m1s_s6/kernels_v3.c : {len(kern)} dòng")
    say(f"    chỉ thị tính năng còn sót: {leaked or 'KHÔNG'}")
    return {"main_lines": len(rest), "kernel_lines": len(kern), "leaked": leaked}
