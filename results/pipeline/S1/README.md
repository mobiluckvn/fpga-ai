# S1 — Bọc luồng có sẵn và tái lập · ĐẠT trên Verilator và tổng hợp · bỏ bước đo kit

Lệnh: `./cdp sim --spec pipeline/specs/s1_{av0,bv1,bv3}.yaml` và `./cdp synth ...`.
Mọi lần chạy dựng **ngoài cây** (`pipeline/work/s1/`, chỉ symlink tới mã nguồn), nên không
một file nào trong `experiment/m1s/`, `rtl/mycore/`, `results/` cũ bị ghi.

## 1. Tái lập trên Verilator — tiêu chí chính của S1

| cấu hình | chu kỳ/ảnh (cdp) | bảng KET_QUA | từng lớp × từng ảnh | CRC 5 tensor × 10 ảnh | SRC_HASH | ms |
|---|---:|---:|---|---|---|---:|
| **A-V0** | **8.987.660** | 8.987.660 | BẰNG TUYỆT ĐỐI | khớp golden | khớp | 332.9 |
| **B-V1** | **1.459.993** | 1.459.993 | BẰNG TUYỆT ĐỐI | khớp golden | khớp | 54.1 |
| **B-V3** | **365.992** | 365.992 | BẰNG TUYỆT ĐỐI | khớp golden | khớp | 13.6 |

## 2. Chu kỳ từng lớp (trung vị 10 ảnh)

| lớp | A-V0 | B-V1 | B-V3 |
|---|---:|---:|---:|
| conv1 | 3.491.721 | 369.909 | 138.213 |
| pool1 | 225.600 | 42.472 | 42.472 |
| conv2 | 5.011.844 | 1.005.419 | 165.152 |
| pool2 | 65.921 | 12.519 | 12.519 |
| dense | 192.552 | 29.652 | 7.614 |
| **tổng** | **8.987.660** | **1.459.993** | **365.992** |

## 3. Firmware dựng lại (dấu vân tay)

| cấu hình | firmware | sha256(firmware.hex) | .text | .bss | RAM |
|---|---|---|---:|---:|---:|
| A-V0 | fw-v0 | `89383bb291c0edac…` | 18.684 | 9.136 | 42.4 % |
| B-V1 | fw-v1 | `88c5a4f059e851a8…` | 20.364 | 9.136 | 45.0 % |
| B-V3 | fw-v1dcr | `7310380cf8df6c9e…` | 19.040 | 12.816 | 48.6 % |

`SRC_HASH` của mọi firmware dựng lại là `c3966b0011df` và firmware **tự khai báo đúng giá trị đó** qua UART.
12/14 cấu hình đã đo của giai đoạn trước dựng từ `main.c` cũ (`647f1d071aca`), nên file hex
mới **không** giống từng byte — nhưng chu kỳ thì bằng tuyệt đối (xem `results/pipeline/S0/`).

## 4. Tổng hợp (yosys + nextpnr) — chi phí và Fmax

| cấu hình | LUT4 (lần này) | LUT4 (đã ghi) | DFF | BSRAM | MULT18X18 | Fmax lần này | Fmax đã ghi |
|---|---:|---:|---:|---:|---:|---:|---:|
| A-V0 | 7.941 | 7.941 | 1.069 | 32 | 0 | 71.76 MHz | 71.76 MHz |
| B-V1 | 3.255 | 3.235 | 573 | 32 | 4 | 56.47 MHz | 53.05 MHz |
| B-V3 | 5.073 | 5.073 | 580 | 32 | 4 | 55.82 MHz | 55.82 MHz |

## 5. Kit — BỎ, theo quyết định của người dùng (2026-10-18)

Lý do: ba cấu hình này đã có số đo kit đầy đủ (10 ảnh × 3 cấu hình trong
`results/experiment/m1s/m1s.csv` và `results/branch_b/m1s_b.csv`), nạp lại chỉ để thấy lại đúng
con số cũ. Phép kiểm đường đo `cdp kit` được gộp vào lần đo thật đầu tiên ở S6.

`cdp kit` đã hiện thực và đã kiểm nhánh "không có kit": dừng ngay, không nạp gì, báo rõ cần cắm kit.
Bitstream của cả ba cấu hình đã dựng sẵn trong cây bóng (`top.fs`), nên khi cần chỉ còn nạp SRAM + đo.

Hệ quả cho tiêu chí S1: *chu kỳ kit = Verilator bằng tuyệt đối* KHÔNG được kiểm lại trong phiên này;
nó đã được kiểm ở giai đoạn trước cho đúng ba cấu hình này (cột `total_sim` của hai CSV đó).

## 6. Sổ cái

Ba dòng `candidates` với `origin=human_replay` (`replay.A-V0`, `replay.B-V1`, `replay.B-V3`).
60 dòng `measurements` nguồn `verilator` = **hai lượt chạy độc lập** × 3 cấu hình × 10 ảnh; hai lượt
cho số giống nhau từng ảnh (lặp lại được). Xuất CSV: `pipeline/db/{ledger,candidates,measurements}.csv`.
