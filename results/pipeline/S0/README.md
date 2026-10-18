# S0 — Khung pipeline CDP · ĐẠT

Lệnh tự kiểm: `./cdp selftest` → `selftest.json`, `selftest.log`, `tool_versions.txt`.
Chạy ngày 2026-10-18, git `98e2093`, `SRC_HASH=c3966b0011df`.

## Tiêu chí ĐẠT của S0 (docs/PIPELINE_PLAN.md) và kết quả

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|---|---|---|
| 1 | `cdp spec pipeline/specs/example_bv3.yaml` hợp lệ | **ĐẠT** — phân giải về cấu hình **B-V3** | `selftest.json` → `checks.spec` |
| 2 | Hai tiến trình cùng xin khoá kit: tiến trình thứ hai **chờ** | **ĐẠT** — A giữ 2 s, B xin sau 0,5 s, B **chờ 1,53 s** rồi mới lấy được | `checks.kitlock` |
| 3 | Sổ cái ghi / đọc / xuất CSV | **ĐẠT** — `pipeline/db/ledger.sqlite` + 3 file CSV | `checks.ledger` |
| 4 | (thêm) Bảng 14 cấu hình của cdp = số đo thật | **ĐẠT** — cả 14 trung vị tính lại từ CSV kit **và** từ `sim.log` đều bằng số trong `docs/KET_QUA_TONG_HOP.md`; chu kỳ kit = Verilator từng ảnh | `checks.targets` |

Định nghĩa trung vị dùng trong cả dự án: `int(statistics.median(10 ảnh))` — đúng như
`scripts/branch_b_table.py`. (`scripts/m1s_check.py` in một trung vị khác, lấy phần tử
thứ 6 của 10, nên lệch ~23 chu kỳ; số trong báo cáo là số của `branch_b_table.py`.)

## Thăm dò cho S1: dựng lại firmware có đổi số chu kỳ không?

12/14 cấu hình đã đo được dựng từ `main.c` cũ (`SRC_HASH=647f1d071aca`); `main.c`
hiện tại là `c3966b0011df` (commit REQ thêm mã trong `#ifdef USE_REQ`). Firmware
nhúng cả `GIT_HASH` và `SRC_HASH` nên **không thể** dựng lại ra file giống từng byte.

Đã kiểm: dựng lại A-V1 từ `main.c` hiện tại rồi chạy trên `rtl/mycore/Vsoc_b1`
(FAST_ADDR=1) cho **đúng từng chu kỳ từng lớp từng ảnh** như `rtl/mycore/bv1/sim.log`
đã ghi.

- log: `recon_rebuild_av1_sim.log` · so sánh: `recon_rebuild_av1.json`
  (`khop_tuyet_doi_tung_lop_tung_anh: true`)

→ S1 có thể đặt tiêu chí "bằng tuyệt đối" mà không bị chặn bởi việc `SRC_HASH` đã đổi.
