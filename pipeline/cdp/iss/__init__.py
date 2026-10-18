"""cdp iss — bộ mô phỏng tập lệnh RV32IM + plugin lệnh tùy biến + mô hình chu kỳ.

CHƯA HIỆN THỰC. Dự kiến ở bước S2:
  core.py                — giải mã RV32IM, CSR cycle/instret, MMIO của soc_b.v
  ext/dot4.py ext/req.py — ngữ nghĩa lệnh tùy biến, lấy ĐÚNG từ rtl/mycore/mycore.v
  timing/mycore.yaml     — chu kỳ theo lớp lệnh (tham số theo FAST_ADDR)
  timing/picorv32.yaml   — hiệu chuẩn từ trace Verilator, mục tiêu sai số <= 2 %
"""
from __future__ import annotations

STEP = "S2"
WHAT = ("ISS RV32IM + plugin dot4/req + mô hình chu kỳ mycore/picorv32, "
        "kiểm trên cả 14 cấu hình")


def main(args, run) -> int:
    run.say("cdp iss: chưa hiện thực — dự kiến ở S2")
    run.say("    " + WHAT)
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
