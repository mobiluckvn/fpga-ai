# Đặc tả quy trình và công cụ — Pipeline đồng thiết kế phần mềm–vi kiến trúc có AI hỗ trợ (CDP)

Tài liệu này định nghĩa **quy trình** (làm gì, theo thứ tự nào, ai/cái gì quyết định) và **công cụ**
(module nào, đầu vào/đầu ra, định dạng). Kế hoạch dựng từng bước có tiêu chí ĐẠT: `docs/PIPELINE_PLAN.md`.
Bối cảnh và số liệu nền: `docs/KET_QUA_TONG_HOP.md` (14 cấu hình, 332,9 → 13,6 ms, 24,6×).

## 0. Nguyên tắc bất di bất dịch

1. **AI đề xuất, công cụ tất định phán quyết.** Không một con số nào (chu kỳ, LUT, Fmax, tăng tốc) được lấy
   từ AI. AI chỉ sinh: biến đổi mã, đặc tả ứng viên, RTL/firmware để kiểm chứng. Mọi số đến từ ISS,
   Verilator, nextpnr hoặc kit.
2. **Đúng từng bit là điều kiện cần.** Mọi biến thể (phần mềm hay phần cứng) phải khớp CRC32 của cả 5 tensor
   với golden Python trước khi số chu kỳ được ghi nhận. Giữ nguyên cơ chế `SRC_HASH` và đối chứng hiện có.
3. **Dự báo trước, đo sau.** Mỗi ứng viên có dự báo (của ISS/mô hình) được ghi vào sổ cái TRƯỚC khi hiện
   thực. Sai số dự báo là dữ liệu nghiên cứu, không được sửa lùi.
4. **Tái lập được.** Mọi lời gọi AI ghi: model/phiên bản, hash prompt, hash đầu vào, đầu ra thô. Mọi lần đo ghi:
   git commit, SRC_HASH, tham số RTL, cờ biên dịch, phiên bản công cụ.
5. **Mù khi kiểm chứng ngược.** Ở các bước "tái khám phá" (S4, S5), AI đề xuất KHÔNG được thấy các tối ưu đã
   làm thủ công (A-V1, bố cục 4 pha, DOT4, REQ, mycore). Thực hiện bằng subagent riêng chỉ được đọc đúng các
   file đầu vào cho phép (mục 4.6).
6. **Một kit, tuần tự.** Mọi truy cập kit qua khoá `pipeline/runs/kit.lock` (flock). Không bao giờ hai tiến
   trình cùng nạp/đo.
7. **Bọc, không viết lại.** Dùng lại Makefile, `scripts/branch_b_measure.sh`, `scripts/m1s_check.py`,
   `scripts/pnr_report.py`, `scripts/riscv_tests.sh`. Không sửa/xoá `feasibility/`, `experiment/m1s/`,
   `rtl/mycore/` hiện có — biến thể mới nằm trong thư mục mới hoặc qua tham số mới (mặc định giữ hành vi cũ).

## 1. Quy trình tổng quát

```
           ┌──────────── Đặc tả thí nghiệm (YAML) ────────────┐
           │ mô hình · firmware · lõi · tham số RTL · ngân sách│
           └──────────────────────┬───────────────────────────┘
                                  ▼
 B1  ┌─ Vòng tối ưu PHẦN MỀM (AI đề xuất biến đổi mã) ──────────────────────┐
     │  đề xuất → build → ISS: đúng bit? chu kỳ? → giữ/loại → lặp đến bão hoà │
     └──────────────────────┬───────────────────────────────────────────────┘
                            ▼  firmware tốt nhất (xác nhận trên Verilator + kit)
 B2  Phân tích tất định: profile 3 tầng + ILP + DLP + bộ nhớ/roofline → analysis.json
                            ▼
     AI sinh ứng viên L1–L5 (+ bộ sinh theo luật để đối chứng) → candidates.json
                            ▼
     Phễu đánh giá: mô hình giải tích → ISS có lệnh/tham số mới → (top-K) RTL Verilator
                    → tổng hợp khối riêng (chi phí) → kit (xác nhận) → [OpenLane, tuỳ chọn]
                            ▼
     Sổ cái: dự báo vs đo · chi phí · trạng thái → hiệu chỉnh mô hình → vòng tiếp theo
```

Năm tầng ứng viên (catalog: `pipeline/catalog/optimizations.yaml`):

| Tầng | Nội dung | Cách đánh giá nhanh |
|---|---|---|
| L1 | Gộp lệnh, lệnh tùy biến vô hướng (REQ, MAX, MIN-MAX clamp, load hậu-tăng) | ISS plugin ngữ nghĩa + độ trễ |
| L2 | Song song dữ liệu (DOT4, MAX4, SIMD 2/4-bit, DOT8 hai thanh ghi) | ISS plugin |
| L3 | Vi kiến trúc: bộ nhớ hai cổng (Harvard) để load/store 1 chu kỳ, nhân 1 chu kỳ, vòng lặp phần cứng, pipeline 2–3 tầng, chuyển tiếp | ISS: đổi tham số mô hình chu kỳ |
| L4 | Khối tăng tốc gắn sát (mảng MAC P×Q có bộ đệm cục bộ) | Mô hình giải tích + ISS lệnh vĩ mô |
| L5 | Tổ chức lõi mới (đa phát lệnh hẹp, dị thể lõi+khối) | Mô hình giải tích; chỉ đề xuất, không bắt buộc hiện thực |

## 2. Kiến trúc công cụ (`pipeline/`, gói Python `cdp`)

Một lệnh CLI: `python -m cdp <lệnh> ...` (hoặc `./cdp`). Mọi lệnh ghi kết quả vào `pipeline/runs/<run_id>/`
và một dòng vào sổ cái `pipeline/db/ledger.sqlite` (kèm bản CSV xuất `pipeline/db/ledger.csv`).

| Lệnh | Module | Việc làm | Đầu vào → Đầu ra |
|---|---|---|---|
| `cdp spec` | `cdp/spec.py` | Kiểm và chuẩn hoá đặc tả thí nghiệm | `specs/*.yaml` → spec đã kiểm |
| `cdp build` | `cdp/build.py` | Build firmware (cờ) + RTL (tham số) bằng Makefile có sẵn | spec → `firmware.elf/.hex`, `SRC_HASH` |
| `cdp iss` | `cdp/iss/` | Bộ mô phỏng tập lệnh RV32IM + plugin lệnh tùy biến + **mô hình chu kỳ theo lõi** | `.elf` + cấu hình lõi → chu kỳ theo lớp, CRC, trace |
| `cdp sim` | `cdp/sim.py` | Chạy Verilator qua Makefile có sẵn | → chu kỳ theo lớp, CRC |
| `cdp kit` | `cdp/kit.py` | Nạp + đo trên kit qua script có sẵn, có khoá kit và đối chứng | → `board.csv` |
| `cdp synth` | `cdp/synth.py` | Tổng hợp **riêng khối mở rộng** (yosys `stat`) để lấy chi phí; tổng hợp toàn SoC để lấy Fmax | → LUT/DFF/MULT/Fmax |
| `cdp profile` | `cdp/profile.py` | Profile 3 tầng từ trace của ISS | trace + `.elf` → `profile.json` |
| `cdp analyze` | `cdp/analyze.py` | ILP (đường găng), DLP (vòng vector hoá được), bộ nhớ (byte/MAC, tái sử dụng), roofline | `profile.json` → `analysis.json` |
| `cdp propose` | `cdp/propose.py` | Tạo gói đầu vào cho AI + kiểm đầu ra theo schema; có `--rules` cho bộ sinh theo luật | `analysis.json` + catalog + prompt → `candidates.json` |
| `cdp estimate` | `cdp/estimate.py` | Dự báo cho từng ứng viên (giải tích + ISS) | `candidates.json` → dự báo ghi sổ cái |
| `cdp verify` | `cdp/verify.py` | Cổng kiểm chứng cho ứng viên đã hiện thực | → ĐẠT/KHÔNG |
| `cdp report` | `cdp/report.py` | Bảng + biểu đồ: dự báo vs đo, Pareto chu kỳ–LUT, roofline, tiến trình B1 | sổ cái → `report/pipeline/` |

### 2.1 ISS và mô hình chu kỳ (trái tim của tốc độ pipeline)
- Python 3, giải mã RV32IM + CSR cycle/instret + MMIO tối thiểu (UART ghi ra bộ đệm, bộ đếm). Nạp `.elf`.
  Nếu quá chậm (> 2 phút cho một ảnh A-V0 ~1,86 triệu lệnh) → tăng tốc bằng bảng giải mã có cache hoặc
  viết lõi giải mã bằng C qua ctypes. Mục tiêu: ≤ 30 s cho một ảnh M1-S.
- **Plugin lệnh**: mỗi lệnh tùy biến là một file `cdp/iss/ext/<ten>.py` khai báo: mã hoá (opcode, funct3,
  funct7), hàm ngữ nghĩa Python, độ trễ theo lõi. **Đây cũng là mô hình tham chiếu** để kiểm RTL ngẫu nhiên
  (một nguồn sự thật duy nhất cho ngữ nghĩa).
- **Mô hình chu kỳ** `cdp/iss/timing/<core>.yaml`: chu kỳ theo lớp lệnh (alu, branch taken/not, jal/jalr,
  load, store, mul, div, custom-*, mmio) + quy tắc đặc biệt (ví dụ PCPI +1). mycore là lõi tất định đơn
  giản → kỳ vọng khớp **tuyệt đối**. PicoRV32 → hiệu chuẩn từ trace Verilator, mục tiêu sai số ≤ 2 %.
  Tham số L3 (load 1 chu kỳ, mul 1 chu kỳ, phạt rẽ nhánh…) chỉ là sửa file timing → dự báo L3 không cần RTL.

### 2.2 Profile ba tầng và phân tích
- Tầng 1 hàm/lớp · Tầng 2 khối cơ bản/vòng lặp (cạnh nhảy ngược) · Tầng 3 mẫu lệnh: phân loại mỗi lệnh động
  thành `mac | load_data | store_data | addr | loop_ctrl | requant | other`, n-gram opcode, chuỗi phụ thuộc.
- ILP: với mỗi khối nóng, đồ thị phụ thuộc dữ liệu (RAW qua thanh ghi) → độ dài đường găng; IPC lý tưởng =
  số lệnh / đường găng (cận trên nếu phát nhiều lệnh).
- DLP: vòng nóng có nạp byte/halfword và chuỗi nhân-cộng → độ rộng phần tử, số làn khả dĩ trong 32 bit,
  yêu cầu thẳng hàng.
- Bộ nhớ: byte nạp/lưu trên mỗi MAC, mức tái sử dụng ước lượng, vị trí trên roofline
  (`MAC/chu kỳ ≤ min(P, B·R/b)`).

## 3. Định dạng dữ liệu (schema trong `pipeline/schemas/`)
- `profile.schema.json`, `analysis.schema.json`, `candidate.schema.json` (đã soạn sẵn bản đầu cho candidate).
- Sổ cái (bảng `candidates`): `id, round, level, origin(ai|rules|human_replay), title, spec_json,
  predicted_cycles, predicted_speedup, predicted_cost_json, status(proposed|estimated|implemented|verified|measured|rejected),
  measured_cycles_sim, measured_cycles_kit, measured_cost_json, fmax_mhz, crc_ok, src_hash, git_commit,
  ai_model, prompt_hash, input_hash, created_at`.
- Bảng `runs`: mọi lần build/ISS/sim/kit với đầy đủ khoá tái lập.

## 4. Vai trò của AI — cụ thể

### 4.1 B1: tối ưu phần mềm
AI nhận: mã C của kernel hiện tại + profile của nó + danh sách biến đổi được phép (thứ tự vòng, bung vòng,
con trỏ chạy, giữ trọng số trong thanh ghi, bố cục dữ liệu/đệm, chia khối, ranh giới hàm `noinline`).
Không được: đổi phép toán số học, đổi mô hình, đổi trọng số, đổi kết quả. Mỗi vòng sinh ≤ 3 biến thể; cái
nào đúng bit và giảm chu kỳ ISS thì giữ. Dừng khi 2 vòng liên tiếp giảm < 2 %.

### 4.2 B2: sinh ứng viên phần cứng
AI nhận **chỉ**: `analysis.json`, `pipeline/catalog/optimizations.yaml`, `pipeline/prompts/propose.md`,
ngân sách tài nguyên, và (từ vòng 2) bảng dự báo-vs-đo của các vòng trước. Trả `candidates.json` đúng schema.

### 4.3 Hiện thực ứng viên
AI (Claude Code) viết RTL + intrinsic + biến thể firmware, nhưng ứng viên chỉ được đo khi qua `cdp verify`:
(1) kiểm ngẫu nhiên ≥ 1 triệu vector so với plugin ISS, (2) `riscv-tests` 48/48, (3) đúng bit M1-S,
(4) ISS = Verilator tuyệt đối với mycore, (5) SRC_HASH khớp.

### 4.4 Bộ sinh theo luật (đối chứng)
`cdp propose --rules`: luật cố định, không AI (ví dụ: mẫu load-byte×2→mul→add lặp ≥ N lần ⇒ đề xuất DOT4;
tỷ lệ load+store > 30 % trên mycore ⇒ đề xuất bộ nhớ hai cổng; …). Dùng để trả lời câu hỏi nghiên cứu:
*AI có đề xuất tốt hơn luật cố định không?*

### 4.5 Ghi nhận
Mọi lần gọi AI lưu `pipeline/runs/<run_id>/ai/{input.json, prompt.md, output.json, meta.json}`.

### 4.6 Chế độ mù
Subagent đề xuất chạy với một thư mục làm việc tạm chỉ chứa các file đầu vào được phép (sao chép vào
`pipeline/runs/<run_id>/sandbox/`). Ghi trong meta.json danh sách file đã cấp. Không cấp `docs/`, `rtl/`,
`experiment/`, `results/`.

## 5. Câu hỏi nghiên cứu pipeline trả lời
- **PQ1** ISS + mô hình chu kỳ dự báo chính xác đến đâu (theo tầng L1/L2/L3)?
- **PQ2** Vòng B1 có AI có tái khám phá (hoặc vượt) tối ưu phần mềm thủ công không (1,45× và 1,29×)?
- **PQ3** B2 có tái khám phá DOT4, REQ, bố cục, và tầng vi kiến trúc (lõi nhanh hơn) từ firmware mù không?
- **PQ4** AI so với bộ sinh theo luật: số ứng viên hữu ích, tăng tốc đạt được trên cùng ngân sách tài nguyên.
- **PQ5** Ứng viên mới (chưa từng làm) đem lại thêm bao nhiêu trên B-V3 (13,6 ms)?
- **PQ6** Tính tổng quát trên mô hình giữ lại.
