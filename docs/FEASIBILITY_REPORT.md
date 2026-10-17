# Báo cáo kiểm chứng tính khả thi — Tang Nano 20K

Ngày bắt đầu: 2026-10-17 · Máy: Mac Intel (x86_64, macOS 26.6.2 build 25G83) · Commit cuối: xem `git log`

## Tổng hợp cổng

| Cổng | Kết quả (ĐẠT / KHÔNG ĐẠT / ĐẠT có dự phòng) | Số đo chính | Dự phòng đã dùng | Log |
|---|---|---|---|---|
| F0 Môi trường | **ĐẠT** | OSS CAD Suite 20261016 (yosys 0.70+145, nextpnr-himbaechel 0.11.1-63, apycula 0.35.dev5, openFPGALoader 1.1.1, verilator 5.053, iverilog 14.0); riscv-none-elf-gcc 15.2.0; JTAG idcode 0x81b = GW2A(R)-18(C); 2 cổng serial | không | results/feasibility/F0/ |
| F1 Blinky | **ĐẠT** | Fmax: 347,58 MHz (ràng buộc 27) · LUT4 30/20736 · DFF 30/15552 · IOB 7/384 · bitstream 730.982 byte · nạp SRAM 3/3 lần OK · người dùng xác nhận LED chạy đúng tốc độ | không | results/feasibility/F1/ |
| F2 UART | | Sai số baud: ; byte lỗi: | | results/feasibility/F2/ |
| F3 BSRAM 64 KB | | Khối BSRAM: /46; Fmax: | | results/feasibility/F3/ |
| F4 DSP | | LUT/DSP (DSP): ; (LUT): | | results/feasibility/F4/ |
| F5 SoC PicoRV32 | | loop kit = sim? ; .text: | | results/feasibility/F5/ |
| F6 Đo lường | | overhead: ; offset hw: | | results/feasibility/F6/ |
| F7 Kernel int8 | | chu kỳ/MAC (conv): | | results/feasibility/F7/ |
| F8 DOT4 qua PCPI | | tăng tốc bài A: ; ΔLUT: ; ΔFmax: | | results/feasibility/F8/ |

## Tài nguyên (từ báo cáo nextpnr)

| Thiết kế | LUT4 | FF | BSRAM | DSP/MULT | Fmax (MHz) |
|---|---|---|---|---|---|
| F1 Blinky | 30 | 30 | 0 | 0 | 347,58 |
| F3 | | | | | |
| F4-DSP | | | | | |
| F4-LUT | | | | | |
| F5 SoC | | | | | |
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

## Tài nguyên tổng của chip (từ report.json của nextpnr, dùng để lập ngân sách các cổng sau)
LUT4 20.736 · DFF 15.552 · ALU 15.552 · IOB 384 · **BSRAM 46** · MULT9X9 96 · **MULT18X18 48** ·
MULT36X36 12 · MULTALU18X18 24 · MULTADDALU18X18 24 · ALU54D 24 · rPLL 2 · BUFG 24 · RAM16SDP4 648

## Kết luận
Go / Go có điều kiện / No-Go: ____
Điều chỉnh đề xuất cho kế hoạch thí nghiệm chính: ____
