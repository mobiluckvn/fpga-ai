# Nhật ký làm việc

Mỗi phiên một mục, mới nhất ở trên cùng:

## 2026-10-17 — Cổng F0 (Môi trường trên Mac) — ĐẠT
- **Làm gì**: dựng toàn bộ môi trường công cụ mã nguồn mở trên máy Mac, `git init`, xác nhận kit được nhận.
- **Máy**: `uname -m` = x86_64 (Intel), macOS 26.6.2 build 25G83 → tải bản **darwin-x64** (không phải arm64).
- **Kết quả / lệnh / output quan trọng**:
  - OSS CAD Suite `2026-10-16` (`oss-cad-suite-darwin-x64-20261016.tgz`) → `~/tools/oss-cad-suite`.
    Gỡ quarantine bằng `./activate` theo README của gói ("Removing quarantine flag from all files and directories... Done").
  - Phiên bản (log: `results/feasibility/F0/tool_versions.txt`): yosys 0.70+145 (a31d95ea0) ·
    nextpnr-himbaechel 0.11.1-63-g44a6c739 · openFPGALoader v1.1.1 · verilator 5.053 devel · iverilog 14.0 devel ·
    `gowin_pack` có sẵn trong gói (apycula 0.35.dev5+g2db53c01c) → **không cần** `pip install apycula`.
  - `nextpnr-himbaechel --list-uarch` → `gatemate, gowin`. Với `--device GW2AR-LV18QN88C8/I7` nó in
    "Using uarch 'gowin' for device 'GW2AR-LV18QN88C8/I7'" → **chuỗi device trong kế hoạch là đúng**.
    `--vopt help` liệt kê `family=`, `cst=`, `ireg_in_iob`, ... đúng như Makefile dự kiến ở F1.
    Có `share/nextpnr/himbaechel/gowin/chipdb-GW2A-18C.bin` → family `GW2A-18C` dùng được.
    (Log: `results/feasibility/F0/uarch_and_synth.txt`, gồm cả `yosys -p 'help synth_gowin'`.)
  - `yosys help synth_gowin`: **không có tùy chọn chọn họ chip**; chỉ có `-top/-json/-nobram/-nolutram/-nodffe/...`.
    Ghi nhận cho F1: lệnh yosys giữ nguyên như kế hoạch, không thêm cờ family.
  - riscv-none-elf-gcc **15.2.0** (xPack v15.2.0-1, darwin-x64) → `~/tools/xpack-riscv-none-elf-gcc-15.2.0-1`.
    Biên dịch thử `-march=rv32im -mabi=ilp32 -O2`: sinh đúng `mul a0,a0,a1` → nhánh M hoạt động
    (log: `results/feasibility/F0/gcc_test.txt`).
  - `.venv` (python 3.14.7) + numpy 2.5.4 + pyserial 3.5.
  - `env/setup_env.sh`: export PATH cho 3 bộ công cụ + biến dùng chung `TN20K_DEVICE/FAMILY/BOARD/FREQ/CST`.
  - **Kit được nhận**: `openFPGALoader --detect -b tangnano20k` → `idcode 0x81b`, Gowin, family GW2A,
    model **GW2A(R)-18(C)**, irlength 8. `--scan-usb` → `0403:6010 FTDI2232 SIPEED "USB Debugger" serial 2025030317`.
    (Log: `results/feasibility/F0/openfpgaloader_detect.txt`.)
  - **Cổng serial**: `/dev/cu.usbserial-20250303170` và `/dev/cu.usbserial-20250303171` (cùng VID:PID 0403:6010,
    hai interface của FT2232). Cả hai mở được @115200, chưa có dữ liệu (đúng, vì FPGA chưa có bitstream).
    (Log: `results/feasibility/F0/serial_ports.txt`.)
  - `git init` xong, `.gitignore` loại `.venv/`, `build/`, `obj_dir/`, `*.fs`, tarball công cụ.
- **Nguồn đã đối chiếu**:
  - README trong gói OSS CAD Suite (`~/tools/oss-cad-suite/README`) — cách gỡ quarantine trên macOS bằng `./activate`.
  - `nextpnr-himbaechel --help`, `--list-uarch`, `--vopt help` (nguồn chính thức của công cụ, thay cho đoán tham số).
  - `yosys -p 'help synth_gowin'`.
  - Chưa đối chiếu chân cắm với repo ví dụ của Sipeed, và chưa đối chiếu Makefile với `examples/himbaechel/`
    của Apicula — **việc này thuộc F1, làm trước lần build đầu** (quy tắc 6 trong CLAUDE.md).
- **Vấn đề, đã thử**: không có lỗi nào phải xử lý. Ghi nhận khác biệt so với kế hoạch:
  máy là **Intel x86_64**, không phải arm64; `gowin_pack` đã có trong gói nên bỏ bước `pip install apycula`.
  Phần cứng USB báo FTDI FT2232 (`0403:6010`) chứ không phải BL616 như CLAUDE.md ghi — không ảnh hưởng,
  JTAG và UART vẫn hiện thành hai cổng `cu.usbserial-*` như mong đợi.
- **Việc tiếp theo / cần người dùng**:
  - F1 (Blinky): đối chiếu `.cst` với ví dụ chính thức của Sipeed, build bằng yosys/nextpnr/gowin_pack,
    nạp SRAM, rồi **cần người dùng xác nhận LED có chạy và chạy đúng tốc độ**.
  - Kit đang cắm và nhận được — giữ nguyên dây/cổng USB này.
