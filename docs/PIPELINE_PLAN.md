# Kế hoạch dựng và đo Pipeline CDP (S0 → S9)

Đặc tả: `docs/PIPELINE_SPEC.md`. Thay thế `docs/CODESIGN_PLAN.md` (giữ lại làm tham khảo).
Mọi quy tắc của `CLAUDE.md` vẫn áp dụng: theo cổng, tối đa 3 hướng sửa rồi dừng hỏi, không bịa số, chỉ nạp SRAM,
commit sau mỗi bước ĐẠT, ghi `docs/LOG.md`. Kết quả từng bước: `results/pipeline/S<n>/`.

Ý tưởng kiểm chứng chính: **tái khám phá mù**. Ta đã biết đáp án do người làm (A-V1, bố cục 4 pha, DOT4, REQ,
lõi mycore). Nếu pipeline đi từ mã thô và lõi gốc mà tự tìm lại được những tối ưu đó (hoặc tốt hơn), đó là bằng
chứng mạnh nhất cho phương pháp. Sau đó mới cho pipeline đi tiếp vào vùng chưa ai làm.

| Bước | Nội dung | Trả lời |
|---|---|---|
| S0 | Khung `cdp`, sổ cái, khoá kit, đặc tả YAML | hạ tầng |
| S1 | Bọc luồng có sẵn: tái tạo đúng 3 dòng đã biết | tái lập |
| S2 | ISS + mô hình chu kỳ, kiểm trên cả 14 cấu hình | PQ1 |
| S3 | Profile 3 tầng + phân tích ILP/DLP/bộ nhớ | nền cho B2 |
| S4 | B1: ĐÃ LÀM THỦ CÔNG (A-V1) — bỏ qua; tái khám phá mù B1 để tuỳ chọn sau S9 | (PQ2 tuỳ chọn) |
| S5 | B2: sinh ứng viên (AI và theo luật), chế độ mù, trên firmware A-V1 + lõi mycore gốc (cấu hình B-V1) | PQ3, PQ4 |
| S6 | Phễu: dự báo → hiện thực top-K → đo kit; vòng mở lần 1 (PMAX4 trên B-V3) | PQ1, PQ5 |
| S7 | Vòng mở lần 2: bộ nhớ hai cổng (B-V4) — ứng viên **mức A** đầu tiên, **ĐẠT** | PQ1, PQ5 |
| S8 | Mô hình giữ lại — **ĐẠT trên Verilator** | PQ6 |
| S9 | Báo cáo tổng hợp, biểu đồ cho bài báo | — |

> **Ghi chú đánh số (sửa 2026-10-18).** Kế hoạch gốc gộp cả vòng mở vào S6 và đặt "mô hình giữ lại" ở S7.
> Thực tế vòng mở sinh ra **hai** ứng viên phần cứng được hiện thực trọn vẹn, mỗi cái một khối lượng
> công việc riêng, và kết quả của cái thứ hai đã nằm ở `results/pipeline/S7/`. Nên tách S7 thành bước
> riêng và dời hai bước cuối xuống S8/S9 — **không đổi tên thư mục kết quả nào**, chỉ cho kế hoạch
> khớp với thực tế đã có trên đĩa.
>
> | thư mục | nội dung | bước theo kế hoạch mới |
> |---|---|---|
> | `results/pipeline/S6/` | `cdp estimate` + PMAX4 (dự báo, hiện thực, đo kit) | S6 |
> | `results/pipeline/S7/` | bộ nhớ hai cổng, B-V4 (K2 của mô hình chi phí) | S7 |
---

## S0 — Khung pipeline
1. Tạo gói `pipeline/cdp/` (Python 3, chỉ dùng thư viện chuẩn + numpy, pyyaml, jsonschema; cài vào `.venv`).
   CLI `python -m cdp`. Lệnh rỗng cho mọi lệnh trong SPEC mục 2 (in "chưa hiện thực").
2. Sổ cái SQLite theo SPEC mục 3, có lệnh `cdp db export` ra CSV.
3. Khoá kit `pipeline/runs/kit.lock` (fcntl.flock), mọi lời gọi kit phải đi qua.
4. Đặc tả YAML: kiểm bằng `pipeline/schemas/spec.schema.json` (tự viết từ ví dụ `pipeline/specs/example_bv3.yaml`).
5. Mỗi lệnh tạo `pipeline/runs/<YYYYMMDD-HHMMSS>-<lệnh>/meta.json` (git commit, phiên bản công cụ, tham số).

**ĐẠT khi**: `python -m cdp spec pipeline/specs/example_bv3.yaml` hợp lệ; hai tiến trình giả lập cùng xin khoá kit
thì tiến trình thứ hai chờ; sổ cái ghi/đọc/xuất CSV được.

## S1 — Bọc luồng có sẵn và tái lập
1. `cdp build`, `cdp sim`, `cdp kit`, `cdp synth` gọi Makefile và script có sẵn (`experiment/m1s/Makefile`,
   `rtl/mycore/Makefile`, `scripts/branch_b_measure.sh`, `scripts/m1s_check.py`, `scripts/pnr_report.py`).
2. Viết đặc tả YAML cho 3 cấu hình: A-V0, B-V1, B-V3.
3. Chạy trọn `build → sim → kit` qua `cdp` cho 3 cấu hình (cần kit, hỏi người dùng nếu kit chưa cắm).

**ĐẠT khi**: chu kỳ từng lớp của 3 cấu hình qua `cdp` **bằng tuyệt đối** số trong `docs/KET_QUA_TONG_HOP.md`
(8.987.660 · 1.459.993 · 365.992), CRC khớp, SRC_HASH khớp; 3 dòng vào sổ cái với origin=`human_replay`.

## S2 — ISS và mô hình chu kỳ
1. `cdp/iss/`: RV32IM, CSR cycle/instret, MMIO cần cho firmware M1-S (UART, bộ đếm, nạp ảnh). Chạy được
   `firmware.elf` của các biến thể hiện có, cho ra CRC 5 tensor giống golden.
2. Plugin lệnh: `dot4`, `req` (đúng ngữ nghĩa RTL hiện có — đọc `rtl/mycore/mycore.v`, `rtl/ext/pcpi_dot4.v`).
3. Mô hình chu kỳ `timing/mycore.yaml` (tham số theo `FAST_ADDR`) và `timing/picorv32.yaml` (hiệu chuẩn từ trace
   Verilator: chu kỳ theo lớp lệnh, PCPI).
4. Chạy ISS trên **cả 14 cấu hình**, so với chu kỳ Verilator từng lớp.

**ĐẠT khi**: CRC ISS = golden cho cả 14; mycore: chu kỳ ISS = Verilator **tuyệt đối** từng lớp; PicoRV32: sai số
từng lớp ≤ 2 % (ghi sai số thật); thời gian ISS cho một ảnh ≤ 30 s (nếu không đạt, ghi số thật và đề xuất tăng tốc).
Bảng sai số vào `results/pipeline/S2/iss_vs_verilator.csv`.

## S3 — Profile và phân tích
1. `cdp profile` từ trace ISS → `profile.json` (3 tầng, SPEC 2.2).
2. `cdp analyze` → `analysis.json`: ILP (đường găng mỗi khối nóng), DLP, byte/MAC, roofline.
3. Chạy cho A-V0, A-V1, B-V1, B-V1+DOT4+C1, B-V3. Viết `results/pipeline/S3/summary.md`.

**ĐẠT khi**: tổng chu kỳ theo profile = ISS; phân loại chu kỳ giải thích được định lượng các hệ số đã đo
(A-V0→A-V1 cắt chủ yếu `addr`/`loop_ctrl`; B-V1→B-V1+DOT4 cắt chủ yếu `mac`+`load_data`; REQ cắt `requant`)
— nêu số cụ thể từ profile cạnh hệ số đo.

## S4 — B1: ĐÃ LÀM, ĐẠT (2026-10-18) — xem `results/pipeline/S4/`
> Ban đầu ghi "bỏ qua vì đã làm thủ công"; người dùng đổi quyết định trong cùng ngày và yêu cầu làm.
> **Kết quả**: AI mù đạt **1,584×** (bản không phụ thuộc dữ liệu) so với **1,355×** của bản thủ công,
> và **2,405×** nếu tính cả bản khai thác tính thưa (phụ thuộc đầu vào, biên độ 13,7 %). 12/12 ứng
> viên đúng từng bit; Verilator xác nhận bằng tuyệt đối. Dừng ở vòng 4 theo quyết định của người dùng,
> chưa tới bão hoà. Rò rỉ phải chặn trước S5: `CLAUDE.md` bị harness chèn vào ngữ cảnh subagent.

### (Phần mô tả gốc, giữ lại)
Tối ưu phần mềm đã làm thủ công: A-V1 (`-DOPT_KERNELS`, 1,45×). Đầu ra của B1 = firmware A-V1.
Bố cục 4 pha (C1) KHÔNG tính vào B1 vì nó chỉ có ý nghĩa khi đã có DOT4 — ở S5 nó là một ứng viên L2
(`L2.layout_for_simd`) cần được tái khám phá. Phần dưới giữ lại làm phương án tuỳ chọn sau S9 (trả lời PQ2).

### (Tuỳ chọn sau S9) B1 tái khám phá mù
1. Điểm xuất phát: mã C thẳng của A-V0 (5 kernel), lõi B-V0 (mycore, không DOT4/REQ) trên ISS.
2. Dựng sandbox mù (SPEC 4.6): chỉ cấp kernel C hiện tại, golden-check tool, profile của nó, danh sách biến
   đổi được phép (SPEC 4.1). KHÔNG cấp `experiment/m1s/main.c` bản tối ưu, KHÔNG cấp docs.
3. Vòng lặp: subagent đề xuất ≤ 3 biến thể/vòng → `cdp build` + ISS → giữ cái đúng bit và nhanh nhất → lặp;
   dừng khi 2 vòng liên tiếp giảm < 2 % hoặc sau 10 vòng. Ghi mọi vòng vào sổ cái (origin=`ai`).
4. Xác nhận biến thể tốt nhất trên Verilator và kit.

**ĐẠT khi**: có đường cong chu kỳ theo vòng; biến thể cuối đúng bit trên kit; báo cáo so với tối ưu thủ công
(A-V1: 1,45×; A-V1+C1). Tái khám phá kém hơn thủ công vẫn là kết quả hợp lệ — ghi rõ khoảng cách và lý do.

## S5 — B2: sinh ứng viên (tái khám phá mù + đối chứng luật)
1. Đầu vào: `analysis.json` của firmware A-V1 chạy trên mycore cấu hình gốc không mở rộng (= B-V1:
   `FAST_ADDR=1, WITH_DOT4=0, WITH_REQ=0`, 1.459.993 chu kỳ, 54,1 ms). Đáp án cần tái khám phá: DOT4, bố cục 4 pha, REQ
   (và, cho tầng L3, các đặc điểm làm mycore nhanh hơn PicoRV32 nếu phân tích chạy thêm trên A-V1/PicoRV32).
2. Subagent mù chạy `pipeline/prompts/propose.md` → `candidates.json` (≥ 8 ứng viên trải ít nhất 3 tầng L1–L5).
   Hai chế độ: `blind_open` (KHÔNG cấp catalog) và `blind_catalog` (cấp catalog) — vì catalog chứa mẫu chung có thể
   làm việc tái khám phá dễ hơn, phải báo cáo riêng. Mỗi chế độ chạy 3 lần độc lập (phiên mới) để đo độ ổn định.
3. `cdp propose --rules` → ứng viên theo luật.
4. Chấm tái khám phá: ứng viên nào tương đương DOT4 / REQ / bố cục 4 pha / bộ nhớ nhanh hơn (lý do mycore nhanh)?

**ĐẠT khi**: 3 tệp candidates AI + 1 tệp luật hợp lệ schema; bảng tái khám phá (có/không, lần chạy nào).

## S6 — Phễu đánh giá và vòng mở lần 1 — ĐẠT (2026-10-18)
1. `cdp estimate` mọi ứng viên S5 (giải tích + ISS: plugin cho L1/L2, sửa timing cho L3). Ghi dự báo vào sổ cái.
2. Chọn top-K (K ≤ 4) theo dự báo tăng tốc / chi phí ước lượng. Hiện thực RTL (tham số mới cho mycore, mặc định
   tắt), qua `cdp verify`, đo kit, `cdp synth` khối riêng.
3. **Vòng mở lần 1**: chạy lại S3→S5→S6 với điểm xuất phát B-V3 (13,6 ms) và không mù (được xem lịch sử).
   Mục tiêu: ứng viên mới chưa từng làm (ví dụ bộ nhớ hai cổng, MAX4, load hậu-tăng, vòng lặp phần cứng,
   nhân 1 chu kỳ). Ứng viên được chọn và hiện thực: **PMAX4**.

**ĐẠT khi**: ≥ 4 ứng viên có cặp (dự báo, đo kit) + chi phí; biểu đồ dự báo-vs-đo; cấu hình nhanh nhất mới
(nếu có) đúng bit trên kit 10 ảnh và 10.000 ảnh.

### Trạng thái — xem `results/pipeline/S6/`
> Bốn cặp (dự báo, đo kit) trong `results/pipeline/S6/du_bao_vs_do.csv`: DOT4, bố cục 4 pha, REQ, PMAX4.
> PMAX4 là ứng viên **đầu tiên do pipeline tự đề xuất** được đo trên kit: **317.878 chu kỳ (28,27×)**,
> dự báo mức B lệch **0,37 %**, 5/5 cổng kiểm ĐẠT.

## S7 — Vòng mở lần 2: bộ nhớ hai cổng (B-V4) — ĐẠT (2026-10-18)
Ứng viên **mức A** đầu tiên: không sửa một dòng mã phần mềm, không thêm lệnh nào — chỉ hạ `λ_load` và
`λ_store` từ 2 về 1 bằng cổng lệnh riêng kiểu Harvard. Vì `n_c` giữ nguyên nên `ΔC = Σ n_c·Δλ_c` là
**đẳng thức**, không phải chặn — đây là phép kiểm **K2** của `docs/MO_HINH_CHI_PHI.md`.
1. Dò khả thi BSRAM hai cổng của GW2AR, đóng băng dự báo **chu kỳ** trước khi viết RTL.
2. Hiện thực `DUAL_PORT=1` (mặc định tắt) + cổng ghi thứ hai của tệp thanh ghi + đường chuyển tiếp `ld_fwd`;
   RAM thu về 32 KB; hai phép đối chứng (liên kết lại 32 KB; đúng từng bit).
3. Verilator + riscv-tests + `cdp synth` cô lập chi phí LUT bằng cặp A/B khác đúng một tham số.
4. Đo trên kit.

**ĐẠT khi**: sai số dự báo mức A được ghi thành số; chi phí LUT quy được về nguyên nhân; đúng bit trên kit.

### Trạng thái: ĐẠT (2026-10-18) — xem `results/pipeline/S7/`
- Dự báo đóng băng **243.641** chu kỳ · Verilator **243.641** · **đo trên kit 243.641** ·
  **sai số 0,00 %** — mức A đúng tuyệt đối, phép kiểm K2 ĐẠT.
- Giá phần cứng: LUT4 **4.459 → 15.736** (×3,5; 75,9 % chip), trong đó **riêng cổng ghi thứ hai +8.724 LUT**
  vì tệp thanh ghi mất khả năng map vào `RAM16SDP4`. Hiệu quả diện tích: PMAX4 **9,8 LUT4** cho mỗi 1 %
  tăng tốc, bộ nhớ hai cổng **370** — chênh 38 lần.
- riscv-tests 48/48 ĐẠT · Fmax 53,01 MHz ĐẠT.
- **Đo kit ĐẠT** (run `20261018-214712-kit`): 2/2 lần đọc, chốt `SRC_HASH`, CRC 10/10,
  kit = Verilator bằng tuyệt đối từng ảnh. Dòng 16 đã vào bảng chính `docs/KET_QUA_TONG_HOP.md`.
- Ràng buộc kéo theo cho S8: RAM còn 32 KB và M1-S đã chiếm 96,4 % (1.180 byte ngăn xếp), nên
  **mô hình giữ lại lớn hơn có thể không vừa trên B-V4** — phải tính trước khi chọn mô hình.

## S8 — Mô hình giữ lại — ĐẠT trên Verilator (2026-10-18), xem `results/pipeline/S8/`
1. Thêm ít nhất một mô hình KHÔNG dùng khi chọn ứng viên (đề xuất: M1-L gấp đôi kênh; nếu kịp, Dense
   autoencoder hoặc KWS DS-CNN rút gọn vừa 64 KB). Golden Python + firmware C thẳng.
2. Chạy B1 (ngắn) rồi áp các ứng viên phần cứng đã chọn ở S6/S7, không chọn lại.

**ĐẠT khi**: bảng tăng tốc mô hình × cấu hình, đúng bit.

### Kết quả
**M1-L** = gấp đôi kênh (16/32): 12.810 tham số, **662.912 MAC = 3,45× M1-S**, int8 98,79 %.
Chạy qua ĐÚNG script huấn luyện, ĐÚNG script lượng tử hoá, ĐÚNG golden, ĐÚNG main.c, ĐÚNG bộ kernel
của M1-S — không một nhánh mã riêng, nên nó "giữ lại" theo nghĩa chặt.

| bước | M1-S | M1-L (giữ lại) | chênh |
|---|---:|---:|---:|
| DOT4 + bố cục 4 pha + REQ | 6,687× | 6,320× | −5,5 % |
| thêm PMAX4 | 1,151× | 1,082× | −6,0 % |
| **tổng** | **7,699×** | **6,841×** | **−11,1 %** |

**Các ứng viên tổng quát hoá được**, mất ~11 % hệ số. Lý do đọc thẳng từ phân rã lớp: gấp đôi kênh
làm conv2 nặng gấp 4 nhưng pooling chỉ gấp 2, nên phần việc PMAX4 chạm tới co từ 15 % xuống 9 %.
**Giá trị của một ứng viên phụ thuộc TỶ LỆ PHÉP TOÁN, không phụ thuộc kích thước mô hình.**

Hai kết quả phụ:
- **PMAX4 làm thời gian chạy hết phụ thuộc dữ liệu**: max-pool bằng C có nhánh nên 10 ảnh cho 10 số
  chu kỳ khác nhau (biên độ tới 0,11 %); với PMAX4 cả 10 ảnh **giống hệt tuyệt đối**. Không nằm trong
  tiêu chí chọn ở S5/S6 — chỉ lộ ra ở đây.
- **B-V4 không có trong bảng**: RAM 32 KB của nó không chứa nổi mô hình nào lớn hơn M1-S (M1-L cần
  48.608 byte). Đây là **giá thứ ba** của bộ nhớ hai cổng, sau chu kỳ và diện tích — và là giá mà cả
  mô hình λ lẫn số LUT đều không thấy. Chỉ có mô hình thứ hai mới làm nó lộ ra.

Ba phép kiểm giống-hệt-từng-bit cho việc tổng quát hoá (weights.h sinh lại giống từng byte; firmware
M1-S giống từng bit; mã máy của kernel tổng quát giống từng bit) — chi tiết trong README của S8.

**Còn thiếu**: chưa đo M1-L trên kit; chưa có dòng PicoRV32 cho M1-L.

## S9 — Báo cáo
`docs/KET_QUA_PIPELINE.md` + `report/pipeline/`: trả lời PQ1–PQ6 bằng số, biểu đồ (dự báo-vs-đo, Pareto
chu kỳ–LUT, tiến trình B1, roofline trước/sau), bảng tái khám phá, chi phí AI (số lần gọi, thời gian).
