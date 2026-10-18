# Danh sách tệp dữ liệu để viết báo cáo

**Mục đích**: gom đúng những tệp cần thiết để viết báo cáo/bài báo về dự án, chuyển sang một
công cụ khác (Claude Desktop) mà không phải mang cả kho.

**Dự án**: TinyML trên lõi RISC-V mềm, FPGA Sipeed Tang Nano 20K (GW2AR-18C), 27 MHz.
Kết quả chính: **332,9 ms → 9,0 ms = 36,89×**, 16 cấu hình đo trên phần cứng thật, mọi lớp
đúng từng bit so với golden Python.

**Bộ lõi: 21 tệp, 172 KB** — đủ để viết trọn báo cáo.

---

## 1. Bộ lõi — gửi đủ bộ này

### 1.1 Tài liệu tổng hợp (đọc trước)

| tệp | KB | nội dung |
|---|---:|---|
| `docs/KET_QUA_PIPELINE.md` | 17,6 | **Quan trọng nhất.** Trả lời PQ1–PQ6 bằng số, mục "điều pipeline KHÔNG làm được", ba loại giá |
| `docs/KET_QUA_TONG_HOP.md` | 16,5 | Bảng 16 cấu hình đo trên kit, điều kiện ghi nhận một dòng |
| `docs/MO_HINH_CHI_PHI.md` | 21,7 | Mô hình `C = Σ n_c·λ_c`, ba mức dự báo A/B/C, các giới hạn ghi **trước** khi đo |
| `docs/PIPELINE_SPEC.md` | 12,3 | Định nghĩa PQ1–PQ6, năm tầng ứng viên L1–L5, đặc tả các lệnh `cdp` |

### 1.2 Kết quả từng bước

| tệp | KB | nội dung |
|---|---:|---|
| `results/pipeline/S2/README.md` | 4,3 | ISS = Verilator tuyệt đối, 14/14 cấu hình |
| `results/pipeline/S3/summary.md` | 15,3 | Profile 3 tầng, phân tích ILP/DLP/roofline |
| `results/pipeline/S4/README.md` | 6,4 | Vòng B1 mù, 1,584× vượt thủ công 1,355× |
| `results/pipeline/S5/README.md` | 7,8 | Tái khám phá mù, 6 lần chạy, AI vs luật |
| `results/pipeline/S6/README_estimate.md` | 7,2 | Phễu dự báo, ba mức |
| `results/pipeline/S6/README_pmax4.md` | 6,2 | PMAX4: dự báo 0,37 % |
| `results/pipeline/S7/README.md` | 11,1 | Bộ nhớ hai cổng: dự báo **0,00 %**, LUT ×3,5 |
| `results/pipeline/S8/README.md` | 12,4 | Mô hình giữ lại M1-L |
| `results/pipeline/S9/README.md` | 4,7 | Quét Pareto + **đính chính con số diện tích PMAX4** |

### 1.3 Dữ liệu số thô (bảng dựng lại được)

| tệp | KB | nội dung |
|---|---:|---|
| `results/pipeline/S6/du_bao_vs_do.csv` | 1,7 | Mọi cặp (dự báo, đo) + sai số — nguồn hình 1 |
| `results/pipeline/S4/duong_cong_b1.csv` | 0,2 | Đường cong B1 từng vòng — nguồn hình 3 |
| `results/pipeline/S8/ket_qua_sim.json` | 1,6 | Mô hình × cấu hình — nguồn hình 4 và 5 |
| `results/pipeline/S9/pareto.json` | 0,9 | Bốn điểm chu kỳ–LUT4 — nguồn hình 2 |
| `results/pipeline/S3/tong_hop_14_cau_hinh.csv` | 1,2 | 14 cấu hình, chu kỳ từng lớp |
| `results/pipeline/S2/n_c_theo_lop.csv` | 7,1 | Số lệnh từng lớp từng cấu hình |
| `results/pipeline/S3/chu_ky_theo_lop_ngu_nghia.csv` | 10,2 | Chu kỳ theo nhãn ngữ nghĩa (mac/load/addr/…) |
| `env/VERSIONS.md` | 5,5 | Phiên bản mọi công cụ — cần cho mục "tái lập" |

---

## 2. Biểu đồ — dùng bản PDF cho bài báo

Thư mục `report/pipeline/`. Mỗi hình có `.pdf` (vector) và `.png` (300 dpi).

| hình | nội dung |
|---|---|
| `hinh1_du_bao_vs_do` | Sai số dự báo theo mức: A = 0,00 %, B trong −34 % … +6 % |
| `hinh2_pareto_chuky_lut` | Pareto chu kỳ ↔ LUT4, bốn cấu hình |
| `hinh3_tien_trinh_b1` | Vòng B1 mù vượt thủ công ở vòng 2 |
| `hinh4_mo_hinh_giu_lai` | Mô hình × cấu hình, mất ~11 % hệ số |
| `hinh5_phan_ra_theo_lop` | Chu kỳ từng lớp, thang log |

Kèm `scripts/s9_figures.py` (12 KB) nếu muốn chỉnh lại hình — nó đọc thẳng từ các CSV/JSON ở
mục 1.3, không có số nào nhập tay.

---

## 3. Bổ sung, chỉ khi cần đào sâu

| tệp | KB | nội dung |
|---|---:|---|
| `results/pipeline/S5/score.json` | 48,7 | Chấm tái khám phá chi tiết từng ứng viên |
| `results/pipeline/S6/estimates_priority.json` | 8,8 | Dự báo top-K |
| `results/pipeline/S6/du_bao_*_truoc_khi_hien_thuc.json` | ~7 | **Dự báo đóng băng**, có dấu thời gian |
| `results/branch_b/m1s_b.csv` | 6,7 | Số đo kit của 14 cấu hình nhánh B |
| `docs/FEASIBILITY_REPORT.md` | 19,0 | Nếu báo cáo cần phần khả thi F0–F8 |
| `AUTHORS.md` | 0,9 | Ghi tên người làm |

---

## 4. Đừng gửi

| tệp | KB | lý do |
|---|---:|---|
| `docs/LOG.md` | 192 | Nhật ký thô từng phiên |
| `results/pipeline/S3/profile.json` | 1.370 | Trace profile đầy đủ |
| `results/branch_b/m1s_b_10000.csv` | 643 | Số đo 10.000 ảnh |
| `results/pipeline/S*/report_*.json` | 50–84 mỗi tệp | Báo cáo nextpnr thô |

Chúng là bằng chứng để tra lại, không phải thứ để đọc khi viết.

---

## 5. Hai điểm phải dặn trước khi giao

1. **Con số diện tích của PMAX4 đã bị RÚT LẠI.** Hai con số `+148 LUT4 (+3,5 %)` và
   `9,8 LUT4 cho mỗi 1 % tăng tốc` không còn hiệu lực: quét lại ở bước S9 trên **cùng một bản
   RTL, cùng firmware, khác đúng một tham số** cho **−181 LUT4**. Chi phí LUT của một lệnh nhỏ
   không đo được bằng một cặp A/B duy nhất (|Δ| < 200 LUT4, dấu không ổn định giữa hai bản RTL).
   Số cũ **vẫn còn trong các tệp cũ kèm ghi chú đính chính** — đừng chép lại nó như số hiện hành.
   Con số của bộ nhớ hai cổng (`+11.277 LUT4`, ×3,5) **vẫn đứng vững** vì lớn gấp ~60 lần dải nhiễu.
   Chi tiết: `results/pipeline/S9/README.md` mục 2.

2. **Khi hai tệp mâu thuẫn, `docs/KET_QUA_PIPELINE.md` thắng.** Mọi số trong đó là bản mới nhất.

---

## 6. Vài con số neo, để kiểm nhanh bản nháp

| | |
|---|---|
| Mô hình chính | M1-S — CNN int8, MNIST, 192.064 MAC, int8 98,25 % |
| Mô hình giữ lại | M1-L — 662.912 MAC (3,45×), int8 98,79 % |
| Mốc đầu | A-V0 trên PicoRV32 — 8.987.660 chu kỳ, 332,9 ms |
| Nhanh nhất | B-V4 — 243.641 chu kỳ, 9,0 ms, **36,89×**, 110,8 ảnh/s |
| Dự báo mức A | 243.641 (đóng băng trước khi viết RTL) = Verilator = kit → **sai 0,00 %** |
| Dự báo mức B | PMAX4 sai +0,37 %; dải chung −34 % … +6 % |
| Vòng B1 mù | 1,584× so với 1,355× của tối ưu thủ công (2,405× nếu tính bản khai thác tính thưa) |
| Tái khám phá mù | DOT4 và "bộ nhớ nhanh hơn" 6/6 lần chạy; bố cục 5/6; REQ 4/6 |
| Mô hình giữ lại | tổng quát hoá, mất ~11 % hệ số (7,699× → 6,841×) |
| Chi phí AI đo được | S5: 5 lời gọi, 34,0 phút tường · S4: 4 vòng, ~1 giờ tường |
| Kit | Sipeed Tang Nano 20K, GW2AR-LV18QN88C8/I7, 27 MHz, LUT4 tổng 20.736, BSRAM 46 |
