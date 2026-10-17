# Nhánh B — lõi RISC-V tự viết: kế hoạch theo cổng

**Câu hỏi nghiên cứu RQ3** (nguyên văn kế hoạch): *"Khả năng chuyển giao: cùng các lệnh đó, khi gắn
vào lõi RISC-V tự viết, có cho mức cải thiện tương đương không?"*

**Tiêu chí ĐẠT của cả nhánh** (nguyên văn kế hoạch): lõi qua `riscv-tests`; 100 ảnh đúng từng bit.
**Phương án dự phòng** (nguyên văn kế hoạch): *"Chỉ báo cáo nhánh A nếu lõi chưa qua bộ kiểm thử."*

## Vì sao nhánh B đáng làm — số liệu nhánh A đã chỉ ra

Đo trên 10.000 ảnh ở biến thể nhanh nhất: **IPC = 0,160** (391.268 lệnh / 2.450.490 chu kỳ). Nghĩa là
trung bình **6,26 chu kỳ cho mỗi lệnh**. Nguyên nhân thuộc **vi kiến trúc**, không thuộc tập lệnh:

- PicoRV32 không có pipeline: mỗi lệnh đi qua một chuỗi trạng thái (fetch → decode → exec → ...).
- Bus trong `soc.v` mất **2 chu kỳ mỗi truy cập** (`S_IDLE` → `S_WAIT`), kể cả nạp lệnh.

Thêm lệnh tùy biến không sửa được hai điều đó. Đây là lý do nhánh B có tiềm năng lớn hơn REQ (1,17×):
nếu đạt IPC 0,6–0,9 thì riêng phần vi kiến trúc đã cho **3,8–5,6×** với **cùng số lệnh**.

Con số này là *tiềm năng*, không phải lời hứa. Nó sẽ được thay bằng số đo.

## Nguyên tắc so sánh: cùng firmware, đúng từng byte

Kế hoạch ghi *"cùng firmware với nhánh A"*. Tôi làm chặt hơn: nhánh B nạp **đúng các file
`firmware.hex` đã dùng ở nhánh A**, không biên dịch lại. Nhờ vậy khi so B-V0 với A-V0 thì **số lệnh
thực thi phải bằng nhau tuyệt đối** (`rdinstret`), và mọi khác biệt về số chu kỳ là **thuần vi kiến
trúc**. Nếu `rdinstret` lệch thì phép so sánh sai — đó là một phép kiểm, không phải chi tiết kỹ thuật.

| Biến thể | Lõi | Firmware dùng lại | Trả lời |
|---|---|---|---|
| B-V0 | lõi tự viết, không lệnh tùy biến | `experiment/m1s/v0/firmware.hex` | RQ3, baseline |
| B-V1 | như trên | `v1/firmware.hex` | tách lợi phần mềm |
| B-V2 | + DOT4 **trong tầng thực thi** | `v2/firmware.hex` | RQ3 |
| B-V1+DOT4 | + DOT4 | `v1d/firmware.hex` | RQ3, điểm so chính với A |
| B-V1+DOT4+C1 | + DOT4 | `v1dc/firmware.hex` | RQ3 |
| B-V3 | + DOT4 + REQ | firmware mới (cả A-V3 cũng chưa làm) | RQ2 + RQ3 |

## Tập lệnh bắt buộc — lấy từ firmware thật, không đoán

Thống kê mã máy của cả 6 bản firmware nhánh A (`objdump`):

- **RV32I đầy đủ**: `lui auipc jal jalr beq bne blt bge bltu bgeu lb lh lw lbu lhu sb sh sw
  addi slti sltiu xori ori andi slli srli srai add sub sll slt sltu xor srl sra or and`
- **Nhân**: `mul` (123), `mulh` (12), `mulhu` (6) — dùng trong requantize kiểu gemmlowp.
- **CSR chỉ đọc**: `rdcycle` (64), `rdcycleh`, `rdinstret` (12) → `csrrs rd, csr, x0`.
- **`fence`** (15) → coi như `nop` (một lõi một luồng, không cache).
- **KHÔNG có `div`/`rem`** trong bất kỳ bản firmware nào.

Vẫn hiện thực `div divu rem remu mulhsu` để qua **trọn bộ** `rv32ui-p` + `rv32um-p`, vì kế hoạch nói
"qua `riscv-tests`" chứ không nói "qua phần liên quan".

## Vi kiến trúc dự kiến

| Quyết định | Chọn | Lý do |
|---|---|---|
| Pipeline | 2 tầng: F (nạp lệnh) ‖ X (giải mã + thực thi + ghi về) | Mục tiêu IPC ≈ 1 khi không truy cập dữ liệu; đủ đơn giản để kiểm được từng bit |
| Bộ nhớ | **1 cổng** BSRAM, đọc đồng bộ 1 chu kỳ | Giữ nguyên `soc.v` cũ thì mất 2 chu kỳ/truy cập; sửa xuống 1 chu kỳ là phần lớn lợi ích |
| Xung đột cổng | `load`/`store` chiếm cổng → chèn 1 bọt khí | Đơn giản, đúng; IPC kỳ vọng ≈ 1/(1+tỷ lệ lệnh truy cập bộ nhớ) |
| Nhân | **Gọi `MULT18X18` trực tiếp**, 4 phép 16×16 ghép thành 32×32→64 | Bài học F4: yosys suy luận DSP cho kết quả **SAI trên kit** |
| Chia | Dịch-trừ 32 chu kỳ | Firmware không dùng; chỉ để qua `riscv-tests` |
| Lệnh tùy biến | Giải mã trong tầng X, **không qua PCPI** | Đúng mục tiêu kế hoạch: "gắn thẳng vào tầng thực thi" |

## Các cổng

| Cổng | Việc | Tiêu chí ĐẠT |
|---|---|---|
| **B0** ✅ | Hạ tầng kiểm thử: lấy `riscv-tests` (ghim commit), dựng thành `.hex`, viết testbench tự kiểm | **Chạy bộ kiểm trên PicoRV32 trước** và tất cả PASS — chứng minh harness đúng trước khi dùng nó xét lõi mới |
| **B1** ✅ | Viết `rtl/mycore/mycore.v` | 100 % `rv32ui-p-*` và `rv32um-p-*` PASS, cùng danh sách với PicoRV32 |
| **B2** ✅ | Chạy firmware M1-S trong Verilator | CRC 5 lớp × 10 ảnh khớp golden; `rdinstret` **bằng tuyệt đối** nhánh A trên cùng file hex |
| **B3** ✅ | Lên kit | Nạp được; 10 ảnh CRC khớp; **kit = Verilator bằng tuyệt đối**; báo LUT4/DFF/BSRAM/Fmax |
| **B4** | B-V2: DOT4 trong tầng thực thi | CRC khớp; đo tăng tốc; so trực tiếp với A-V2/A-V1+DOT4 → **RQ3** |
| **B5** | B-V3: lệnh REQ | CRC khớp; đo; so với dự báo 1,17× ở nhánh A |
| **B6** | Tổng kết | **100 ảnh đúng từng bit** trên kit; bảng tài nguyên/Fmax/chu kỳ A ↔ B; kết luận RQ3 |

Quy tắc chung của dự án vẫn áp dụng: mỗi cổng mô phỏng trước khi tổng hợp, tối đa 3 hướng sửa rồi
dừng và hỏi, chỉ nạp SRAM, không bịa số, cập nhật `docs/LOG.md` và commit sau mỗi cổng.

## Rủi ro đã nhận diện trước

| Rủi ro | Dấu hiệu sớm | Phương án |
|---|---|---|
| Bộ nhân DSP sai trên kit (đã gặp ở F4) | Verilator đúng, kit sai | Gọi `MULT18X18` trực tiếp ngay từ đầu, không nhờ yosys suy luận |
| Lõi 2 tầng không đạt 27 MHz | Fmax trong báo cáo nextpnr < 27 | Cắt đường tổ hợp dài nhất (nhân, dịch) thành 2 chu kỳ |
| Hết LUT4 (nhánh A đã dùng 38,9 %) | nextpnr báo quá tài nguyên | Bỏ `div`/`rem` khỏi bản lên kit (firmware không dùng), giữ trong bản mô phỏng |
| `riscv-tests` cần bẫy/CSR máy | Bài kiểm treo | Dùng môi trường kiểm rút gọn kiểu `picorv32/tests` (PASS/FAIL bằng ghi vào địa chỉ quy ước) |
