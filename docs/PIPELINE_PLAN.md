# Kế hoạch dựng và đo Pipeline CDP (S0 → S8)

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
| S4 | B1: ĐÃ LÀM THỦ CÔNG (A-V1) — bỏ qua; tái khám phá mù B1 để tuỳ chọn sau S8 | (PQ2 tuỳ chọn) |
| S5 | B2: sinh ứng viên (AI và theo luật), chế độ mù, trên firmware A-V1 + lõi mycore gốc (cấu hình B-V1) | PQ3, PQ4 |
| S6 | Phễu: dự báo → hiện thực top-K → đo kit; vòng mở (ứng viên mới trên B-V3) | PQ1, PQ5 |
| S7 | Mô hình giữ lại | PQ6 |
| S8 | Báo cáo tổng hợp, biểu đồ cho bài báo | — |

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

## S4 — B1: ĐÃ LÀM THỦ CÔNG → bỏ qua (quyết định của người dùng, 2026-10-18)
Tối ưu phần mềm đã làm thủ công: A-V1 (`-DOPT_KERNELS`, 1,45×). Đầu ra của B1 = firmware A-V1.
Bố cục 4 pha (C1) KHÔNG tính vào B1 vì nó chỉ có ý nghĩa khi đã có DOT4 — ở S5 nó là một ứng viên L2
(`L2.layout_for_simd`) cần được tái khám phá. Phần dưới giữ lại làm phương án tuỳ chọn sau S8 (trả lời PQ2).

### (Tuỳ chọn sau S8) B1 tái khám phá mù
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

## S6 — Phễu đánh giá và vòng mở
1. `cdp estimate` mọi ứng viên S5 (giải tích + ISS: plugin cho L1/L2, sửa timing cho L3). Ghi dự báo vào sổ cái.
2. Chọn top-K (K ≤ 4) theo dự báo tăng tốc / chi phí ước lượng. Hiện thực RTL (tham số mới cho mycore, mặc định
   tắt), qua `cdp verify`, đo kit, `cdp synth` khối riêng.
3. **Vòng mở**: chạy lại S3→S5→S6 với điểm xuất phát B-V3 (13,6 ms) và không mù (được xem lịch sử). Mục tiêu:
   ứng viên mới chưa từng làm (ví dụ bộ nhớ hai cổng, MAX4, load hậu-tăng, vòng lặp phần cứng, nhân 1 chu kỳ).

**ĐẠT khi**: ≥ 4 ứng viên có cặp (dự báo, đo kit) + chi phí; biểu đồ dự báo-vs-đo; cấu hình nhanh nhất mới
(nếu có) đúng bit trên kit 10 ảnh và 10.000 ảnh.

## S7 — Mô hình giữ lại
1. Thêm ít nhất một mô hình KHÔNG dùng khi chọn ứng viên (đề xuất: M1-L gấp đôi kênh; nếu kịp, Dense
   autoencoder hoặc KWS DS-CNN rút gọn vừa 64 KB). Golden Python + firmware C thẳng.
2. Chạy B1 (ngắn) rồi áp các ứng viên phần cứng đã chọn ở S6, không chọn lại.

**ĐẠT khi**: bảng tăng tốc mô hình × cấu hình, đúng bit.

## S8 — Báo cáo
`docs/KET_QUA_PIPELINE.md` + `report/pipeline/`: trả lời PQ1–PQ6 bằng số, biểu đồ (dự báo-vs-đo, Pareto
chu kỳ–LUT, tiến trình B1, roofline trước/sau), bảng tái khám phá, chi phí AI (số lần gọi, thời gian).
