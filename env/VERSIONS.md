# Phiên bản công cụ

Ghim tại F0 (2026-10-17). Log thô: `results/feasibility/F0/`.
Nạp môi trường: `source env/setup_env.sh`.

## Máy
- macOS 26.6.2 (build 25G83), `uname -m` = **x86_64** (Intel) → dùng mọi bản tải **darwin-x64**.

## OSS CAD Suite
- Gói: `oss-cad-suite-darwin-x64-20261016.tgz` (release tag `2026-10-16`), cài tại `~/tools/oss-cad-suite`
- `VERSION` = **20261016**
- yosys: **0.70+145** (git sha1 `a31d95ea0`)
- nextpnr-himbaechel: **nextpnr-0.11.1-63-g44a6c739** — uarch khả dụng: `gatemate, gowin`
- apycula (cung cấp `gowin_pack`): **0.35.dev5+g2db53c01c** (bundled, không cần `pip install apycula`)
- openFPGALoader: **v1.1.1**
- verilator: **5.053 devel rev v5.052-448-g1272f7355 (mod)**
- iverilog: **14.0 (devel) s20260301-583-g5d7612759-dirty**
- chipdb có sẵn cho họ chip đích: `chipdb-GW2A-18C.bin`, `chipdb-GW2A-18.bin`

## Toolchain RISC-V
- xPack GNU RISC-V Embedded GCC **15.2.0** (release `v15.2.0-1`), bản `darwin-x64`
- Cài tại `~/tools/xpack-riscv-none-elf-gcc-15.2.0-1`
- Đã thử biên dịch `-march=rv32im -mabi=ilp32`: sinh đúng lệnh `mul` (xem `results/feasibility/F0/gcc_test.txt`)

## Python
- python3 hệ thống: **3.14.7** → venv dự án tại `.venv`
- numpy **2.5.4**, pyserial **3.5**
- PyTorch: chưa cài (chỉ cài khi tới giai đoạn mô hình)

## Mã nguồn ngoài
- picorv32: chưa lấy (sẽ ghi commit hash ở F5)

## Thông số luồng Gowin đã xác nhận ở F0
| Tham số | Giá trị | Nguồn xác nhận |
|---|---|---|
| nextpnr `--device` | `GW2AR-LV18QN88C8/I7` | nextpnr nhận chuỗi này: "Using uarch 'gowin' for device 'GW2AR-LV18QN88C8/I7'" |
| `--vopt family=` | `GW2A-18C` | có `chipdb-GW2A-18C.bin`; `--vopt family=` là tùy chọn hợp lệ của uarch gowin |
| `gowin_pack -d` | `GW2A-18C` | `gowin_pack -h` |
| openFPGALoader `-b` | `tangnano20k` | `--detect -b tangnano20k` chạy thành công |

## Phần cứng nhận được (F0)
- USB: `0403:6010` FTDI2232, nhà sản xuất `SIPEED`, sản phẩm `USB Debugger`, serial `2025030317`
- JTAG idcode `0x81b` → Gowin, family GW2A, model **GW2A(R)-18(C)**, irlength 8
- Cổng serial: `/dev/cu.usbserial-20250303170` và `/dev/cu.usbserial-20250303171`
  (cả hai mở được @115200; chưa biết cổng nào là UART của FPGA — xác định ở F2)
