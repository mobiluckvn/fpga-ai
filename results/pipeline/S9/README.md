# S9 — báo cáo tổng hợp, biểu đồ, và một phép quét diện tích làm lộ giới hạn của phép đo cũ

Báo cáo: `docs/KET_QUA_PIPELINE.md` · Biểu đồ: `report/pipeline/` · Script: `scripts/s9_figures.py`

## 1. Quét Pareto trên MỘT bản RTL, MỘT firmware

Để biểu đồ chu kỳ–diện tích có nghĩa, bốn điểm phải đến từ cùng một bản RTL. Ba điểm được
tổng hợp lại ở bước này (`p9_v1`, `p9_v3`, `p9_pmax4`), dùng **cùng firmware `gs_dcrp`** và
khác nhau **đúng ở tham số `chparam`**. Điểm thứ tư (B-V4) dùng cặp A/B riêng `bs7ref`/`bs7dp`
của S7, vì bộ nhớ hai cổng chỉ có 32 KB nên không chạy được cùng firmware.

| cấu hình | `WITH_DOT4` | `WITH_REQ` | `WITH_PMAX4` | `DUAL_PORT` | LUT4 | Fmax | chu kỳ/ảnh (kit) |
|---|---|---|---|---|---:|---:|---:|
| B-V1 | 0 | 0 | 0 | 0 | **3.054** | 54,37 | 1.459.993 |
| B-V3 | 1 | 1 | 0 | 0 | **4.640** | 61,30 | 365.992 |
| B-V3+PMAX4 | 1 | 1 | **1** | 0 | **4.459** | 59,08 | 317.878 |
| B-V4 | 1 | 1 | 1 | **1** | **15.736** | 53,01 | 243.641 |

## 2. Phát hiện: bật PMAX4 làm GIẢM 181 LUT4

`p9_v3` và `p9_pmax4` khác nhau **đúng một tham số** (`WITH_PMAX4` 0 → 1), cùng file RTL,
cùng firmware, cùng mọi thứ khác — đã đối chiếu dòng `chparam` trong hai `yosys.log`. Kết quả:

    LUT4  4.640  →  4.459      (−181, tức bật thêm một lệnh lại TỐN ÍT HƠN)

Điều này **mâu thuẫn với con số `+148 LUT4` đã ghi ở S6** cho đúng lệnh đó, đo bằng đúng
kiểu cặp A/B, chỉ khác là trên bản RTL thời điểm ấy.

### Đây không phải ngẫu nhiên

Tổng hợp là **tất định** khi tham số giống nhau — đã kiểm bằng ba lần dựng độc lập cho cùng
một bộ tham số, ở ba thư mục khác nhau với **ba firmware khác nhau**:

| lần dựng | firmware | LUT4 |
|---|---|---:|
| `bs7ref` (S7) | `cdp32` (M1-S, 32 KB) | 4.459 |
| `gl_dcrp` (S8) | M1-L, 64 KB | 4.459 |
| `p9_pmax4` (S9) | `gs_dcrp` (M1-S, 64 KB) | 4.459 |

Ba con số **giống hệt nhau**. Nên: (a) nội dung firmware **không** ảnh hưởng số LUT4, đúng như
mong đợi vì nó chỉ là dữ liệu khởi tạo BSRAM; (b) luồng tổng hợp lặp lại được.

### Vậy nguyên nhân là gì

Đổi một tham số **đổi netlist**, và trình tối ưu/đóng gói của yosys bám theo netlist. Với một
lệnh nhỏ như PMAX4, phần logic nó thêm vào **cùng bậc độ lớn** với mức xê dịch mà việc đóng gói
lại gây ra. Hệ quả:

> **Chi phí LUT của một lệnh nhỏ KHÔNG đo được bằng một cặp A/B duy nhất.** Với PMAX4,
> |Δ| < 200 LUT4 (dưới 1 % của chip) và **dấu còn không ổn định** giữa hai bản RTL.

### Hệ quả cho các con số đã công bố

| con số cũ | trạng thái |
|---|---|
| "PMAX4 tốn **+148 LUT4** (+3,5 %)" | **rút lại** — nằm trong dải nhiễu, bản RTL hiện tại cho −181 |
| "PMAX4 tốn **9,8 LUT4** cho mỗi 1 % tăng tốc" | **rút lại** — dẫn xuất từ con số trên |
| "bộ nhớ hai cổng tốn **+11.277 LUT4** (×3,5)" | **giữ** — lớn gấp ~60 lần dải nhiễu |
| "riêng cổng ghi thứ hai tốn +8.724 LUT4 (77 %)" | **giữ** — cùng lý do |

Kết luận định tính **không đổi và còn mạnh hơn**: PMAX4 rẻ tới mức **không đo nổi** bằng phương
pháp này, còn bộ nhớ hai cổng đắt tới mức không thể nhầm. Điều phải bỏ là việc gán cho PMAX4
một con số diện tích cụ thể.

### Cách đo đúng cho lần sau (chưa làm)

Muốn con số có nghĩa thì phải tổng hợp **riêng khối** đó (`cdp synth` khối độc lập, không nhúng
trong lõi), hoặc lấy **trung vị trên nhiều bản RTL/seed** để tách tín hiệu khỏi nhiễu đóng gói.

## 3. Biểu đồ

| hình | nội dung | nguồn số |
|---|---|---|
| `hinh1_du_bao_vs_do` | sai số dự báo theo mức A/B | `S6/du_bao_vs_do.csv` |
| `hinh2_pareto_chuky_lut` | Pareto chu kỳ–LUT4 | `S9/pareto.json` (mục 1) |
| `hinh3_tien_trinh_b1` | tiến trình vòng B1 mù | `S4/duong_cong_b1.csv` |
| `hinh4_mo_hinh_giu_lai` | mô hình × cấu hình | `S8/ket_qua_sim.json` |
| `hinh5_phan_ra_theo_lop` | chu kỳ từng lớp, thang log | `S8/ket_qua_sim.json` |

Mỗi hình có bản PNG 300 dpi và PDF vector. `scripts/s9_figures.py` đọc thẳng từ các tệp kết quả
— không có số nào nhập tay.

## 4. Tệp

| tệp | nội dung |
|---|---|
| `pareto.json` | bốn điểm chu kỳ–LUT4 kèm đường dẫn tệp nguồn của từng số |
| `sweep/` | `report.json` + `yosys.log` của ba lần tổng hợp `p9_*` |
