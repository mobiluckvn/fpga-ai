# Báo cáo kiểm chứng tính khả thi — Tang Nano 20K

Ngày bắt đầu: 2026-10-17 · Máy: Mac Intel (x86_64, macOS 26.6.2 build 25G83) · Commit cuối: xem `git log`

## Tổng hợp cổng

| Cổng | Kết quả (ĐẠT / KHÔNG ĐẠT / ĐẠT có dự phòng) | Số đo chính | Dự phòng đã dùng | Log |
|---|---|---|---|---|
| F0 Môi trường | **ĐẠT** | OSS CAD Suite 20261016 (yosys 0.70+145, nextpnr-himbaechel 0.11.1-63, apycula 0.35.dev5, openFPGALoader 1.1.1, verilator 5.053, iverilog 14.0); riscv-none-elf-gcc 15.2.0; JTAG idcode 0x81b = GW2A(R)-18(C); 2 cổng serial | không | results/feasibility/F0/ |
| F1 Blinky | | Fmax: | | results/feasibility/F1/ |
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

## Kết luận
Go / Go có điều kiện / No-Go: ____
Điều chỉnh đề xuất cho kế hoạch thí nghiệm chính: ____
