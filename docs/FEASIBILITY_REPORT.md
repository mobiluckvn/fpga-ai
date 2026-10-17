# Báo cáo kiểm chứng tính khả thi — Tang Nano 20K

Ngày bắt đầu: 2026-10-17 · Máy: Mac Intel (x86_64, macOS 26.6.2 build 25G83) · Commit cuối: xem `git log`

## Tổng hợp cổng

| Cổng | Kết quả (ĐẠT / KHÔNG ĐẠT / ĐẠT có dự phòng) | Số đo chính | Dự phòng đã dùng | Log |
|---|---|---|---|---|
| F0 Môi trường | **ĐẠT** | OSS CAD Suite 20261016 (yosys 0.70+145, nextpnr-himbaechel 0.11.1-63, apycula 0.35.dev5, openFPGALoader 1.1.1, verilator 5.053, iverilog 14.0); riscv-none-elf-gcc 15.2.0; JTAG idcode 0x81b = GW2A(R)-18(C); 2 cổng serial | không | results/feasibility/F0/ |
| F1 Blinky | **ĐẠT** | Fmax: 347,58 MHz (ràng buộc 27) · LUT4 30/20736 · DFF 30/15552 · IOB 7/384 · bitstream 4.618.782 byte (không nén) · nạp SRAM 3/3 lần OK · người dùng xác nhận LED chạy đúng tốc độ | bỏ `gowin_pack -c` | results/feasibility/F1/ |
| F2 UART | **ĐẠT** | Sai số baud: +0,1603 % (DIV=234 → 115.384,62 baud); byte lỗi: **0/10.240** · cổng UART = `/dev/cu.usbserial-20250303171` · Fmax 187,48 MHz · bộ đếm FPGA: rx+10.240, dr=0, er=0, ov=0, FIFO hwm 1/63 · 5.248 B/s | khối ghi của host ≤66 byte (giới hạn cầu FT2232/macOS, không phải của FPGA) | results/feasibility/F2/ |
| F3 BSRAM 64 KB | **ĐẠT** | Khối BSRAM: **32/46** (69,6 %); Fmax: **157,36 MHz** · CRC32 ROM=C7CD86AA và RW=D63B5AB4 **khớp Python 3/3 lần đọc** · thêm phép phản chứng: đổi hạt giống LFSR → CRC ROM đổi đúng thành 454701B8, CRC RW giữ nguyên | **không** | results/feasibility/F3/ |
| F4 DSP | **ĐẠT có dự phòng** | acc=FEF834C3 khớp Python 3/3 lần với biến thể **PRM** (gọi trực tiếp MULT18X18) và **LUT**; **sai** với cả hai biến thể để yosys tự suy luận DSP. LUT4: PRM 811 / LUT 1764; Fmax: PRM 233,64 / LUT 73,08 MHz | **có**: không dùng DSP do yosys suy luận; phải gọi primitive MULT18X18 trực tiếp | results/feasibility/F4/ |
| F5 SoC PicoRV32 | **ĐẠT** | loop kit = sim? **CÓ, bằng tuyệt đối** (14.006 chu kỳ, 3/3 lần đọc; thêm 7 khoá nữa cũng khớp tuyệt đối) ; .text: **1.220 byte** · BSRAM 32/46 · LUT4 7.950/20.736 · Fmax 70,05 MHz | `synth_gowin -nodsp` (bắt buộc, do kết quả F4) | results/feasibility/F5/ |
| F6 Đo lường | | overhead: ; offset hw: | | results/feasibility/F6/ |
| F7 Kernel int8 | | chu kỳ/MAC (conv): | | results/feasibility/F7/ |
| F8 DOT4 qua PCPI | | tăng tốc bài A: ; ΔLUT: ; ΔFmax: | | results/feasibility/F8/ |

## Tài nguyên (từ báo cáo nextpnr)

| Thiết kế | LUT4 | FF | BSRAM | DSP/MULT | Fmax (MHz) |
|---|---|---|---|---|---|
| F1 Blinky | 30 | 30 | 0 | 0 | 347,58 |
| F2 UART | 883 | 236 | 0 (8× RAM16SDP4 cho FIFO) | 0 | 187,48 |
| F3 BSRAM 64 KB | 865 | 207 | **32/46** | 0 | 157,36 |
| F3 | | | | | |
| F4-DSP (yosys suy luận, SAI) | 771 | 291 | 0 | 4× MULT9X9 | 225,28 |
| F4-D18 (18 bit, SAI) | 815 | 291 | 0 | 4× MULT9X9 | 237,02 |
| **F4-PRM (MULT18X18 trực tiếp, ĐÚNG)** | **811** | 291 | 0 | **4× MULT18X18** | **233,64** |
| F4-LUT (-nodsp, ĐÚNG) | 1764 | 291 | 0 | 0 | 73,08 |
| F5 SoC | 7950 | 1069 | 32/46 | 0 (nhân 32×32 bằng LUT vì -nodsp) | 70,05 |
| F8 SoC + DOT4 | | | | | |

## Số đo F7/F8 (kit, 27 MHz)

| Bài | Biến thể | Chu kỳ | hw_count | instret | CPI | CRC khớp |
|---|---|---|---|---|---|---|
| A dot 1024 ×100 | C thẳng | | | | | |
| A dot 1024 ×100 | DOT4 | | | | | |
| B conv1 28×28×8 | C thẳng | | | | | |

Ước tính thô M1-S (ghi rõ cách ngoại suy): ____

## Vấn đề gặp phải và cách xử lý
(tóm tắt từ LOG.md)

- F0: máy là Intel x86_64 (không phải arm64) → dùng mọi gói bản `darwin-x64`. `gowin_pack` đã có sẵn
  trong OSS CAD Suite nên bỏ được bước `pip install apycula`.
- F1: `synth_gowin` của Yosys **mặc định `-family gw1n`** → bắt buộc truyền `-family gw2a` cho GW2AR-18.
  Phát hiện khi đối chiếu `examples/Makefile` của Apicula, trước lần build đầu.
- F2: **bitstream nén (`gowin_pack -c`) của apycula 0.35.dev5 không nạp được** bằng openFPGALoader v1.1.1
  cho thiết kế F2: `FsParser: checksum data is truncated` (tái lập 2/2 lần). Bản không nén nạp bình thường
  → đã bỏ `-c` khỏi luồng của mọi cổng. (F1 nén thì nạp được, nên lỗi phụ thuộc thiết kế.)
- F2: **cầu USB FT2232 / driver macOS mất byte ở chiều FPGA→PC khi host ghi ≥67 byte trong một `write()`**.
  Bộ đếm bên trong FPGA chứng minh FPGA vẫn nhận đủ (rx tăng đúng) và phát đủ (tx = echo + thông báo),
  với dr=0, er=0, ov=0, mức FIFO cao nhất chỉ 1/63 — tức lỗi nằm ngoài FPGA. Dùng luồng đọc riêng trên host
  KHÔNG cứu được. Khối ghi lớn nhất còn nguyên vẹn: **66 byte**; luồng đo dùng 64 byte (một gói USB).
  Ảnh hưởng về sau: kênh thu số đo (FPGA→PC) không bị ảnh hưởng; mọi script ghi dữ liệu PC→FPGA
  phải chia khối ≤64 byte.

## Tài nguyên tổng của chip (từ report.json của nextpnr, dùng để lập ngân sách các cổng sau)
LUT4 20.736 · DFF 15.552 · ALU 15.552 · IOB 384 · **BSRAM 46** · MULT9X9 96 · **MULT18X18 48** ·
MULT36X36 12 · MULTALU18X18 24 · MULTADDALU18X18 24 · ALU54D 24 · rPLL 2 · BUFG 24 · RAM16SDP4 648

## Ghi chú quan trọng sau F5 — nền tảng CPU đã có
`F5,loop` trên kit **bằng tuyệt đối** Verilator (14.006 chu kỳ cho `busy_loop(1000)`), và 7 khoá khác
cũng khớp tuyệt đối: `hello`, `loopn`, `hwc` (14.035), `instret` (2.004), `arith` (C91C7978),
`ram` (EFEEC031), `done` — lặp lại 3/3 lần đọc độc lập. Nghĩa là:
- Phương pháp đo chu kỳ bằng `rdcycle` cho cùng con số trên mô phỏng và phần cứng.
- Chênh giữa bộ đếm phần cứng và `rdcycle` là **29 chu kỳ** (14.035 − 14.006) — F6 sẽ kiểm xem hằng
  số này có giữ nguyên ở mọi độ dài đoạn đo hay không.
- `arith` khớp ⇒ **lệnh MUL/DIV cho kết quả đúng trên kit**, tức việc buộc `-nodsp` (hệ quả của F4)
  đã xử lý được rủi ro bộ nhân. Giá phải trả: LUT4 7.950/20.736 (38,3 %) và Fmax 70,05 MHz.
- `ram` khớp ⇒ phần `.rodata` của firmware được nạp đúng vào BSRAM qua `$readmemh`.

## Ghi chú quan trọng sau F4 — cách dùng khối nhân
Bảng chi tiết: `results/feasibility/F4/comparison.md`.

**Không được dựa vào việc yosys tự suy luận DSP cho phép nhân int8 có dấu trên chip này.**
Với `synth_gowin` mặc định, yosys ánh xạ `$signed(a8) * $signed(b8)` vào `MULT9X9` và kết quả trên kit
**sai byte cao của từng tích** (8 bit thấp vẫn đúng). Cùng RTL đó, `-nodsp` cho kết quả đúng, nên lỗi
nằm ở đường suy luận/ánh xạ DSP, không ở RTL.

Cách dùng được, đã kiểm trên kit: **gọi trực tiếp primitive `MULT18X18` ở chế độ không dấu
(`ASIGN=BSIGN=0`) với toán hạng int8 đã mở rộng dấu lên 18 bit**, rồi đọc `DOUT[17:0]` như số có dấu
18 bit. Đúng về mặt số học vì x'·y' ≡ x·y (mod 2^18) và |x·y| ≤ 16384 < 2^17.

Đổi lại, dùng DSP tiết kiệm **953 LUT4** (811 so với 1764) và cho Fmax **cao hơn 3,2 lần**
(233,64 so với 73,08 MHz) so với nhân bằng logic. → **F8 (DOT4) nên dùng cách PRM.**

## Ghi chú quan trọng sau F3
Rủi ro lớn nhất của dự án (BSRAM 64 KB có khởi tạo sẵn qua luồng mã nguồn mở) đã được **giải quyết, không
phải dùng phương án dự phòng nào** trong bốn phương án (a)–(d) của FEASIBILITY_PLAN. Yosys tự suy luận
`$readmemh` + `reg [31:0] mem[0:16383]` thành 32 khối BSRAM có nội dung khởi tạo, gowin_pack nạp nội dung
đó vào bitstream, và kit đọc lại đúng từng bit. Còn **14/46 khối BSRAM (30 %) dư** cho các cổng sau.

## Kết luận
Go / Go có điều kiện / No-Go: ____
Điều chỉnh đề xuất cho kế hoạch thí nghiệm chính: ____
