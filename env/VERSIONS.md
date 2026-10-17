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

## Trình biên dịch C++ của máy (cho Verilator)
- Apple clang **21.0.0** (clang-2100.1.1.101), Command Line Tools **26.5.0**.
- **Lỗi môi trường đã gặp ở F5**: `/Library/Developer/CommandLineTools/usr/include/c++/v1`
  thiếu nội dung nên `clang++` không tìm được `<cstddef>` → Verilator không biên dịch được.
  libc++ vẫn có trong SDK. `env/setup_env.sh` tự phát hiện và đặt
  `TN20K_CXX_INC=-I$(xcrun --show-sdk-path)/usr/include/c++/v1`, Makefile của F5 truyền
  cờ này cho verilator qua `-CFLAGS`.

## Python
- python3 hệ thống: **3.14.7** → venv dự án tại `.venv` (đo lường, script kiểm tra)
- numpy **2.5.4**, pyserial **3.5**

### venv riêng cho phần mô hình: `.venv-model`
- **Python 3.12.13** (`brew python@3.12`) + **torch 2.2.2** + **numpy 1.26.4**
- Vì sao phải tách: Python 3.14 **không có** wheel torch cho macOS x86_64
  (`pip install torch` → "No matching distribution found"). torch **2.2.2** là bản cuối
  còn wheel cho macOS x86_64, và nó biên dịch với NumPy 1.x nên **bắt buộc `numpy<2`**
  (với numpy 2.5.4 thì `import torch` báo "A module that was compiled using NumPy 1.x
  cannot be run in NumPy 2.5.4").
- Dùng cho: `model/train_m1s.py`, `model/quantize_m1s.py`. Mọi script đo vẫn dùng `.venv`.

## Dữ liệu MNIST (model/data/, 4 file idx.gz)
Nguồn: `https://storage.googleapis.com/cvdf-datasets/mnist/`
```
440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609  train-images-idx3-ubyte.gz
3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c  train-labels-idx1-ubyte.gz
8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6  t10k-images-idx3-ubyte.gz
f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6  t10k-labels-idx1-ubyte.gz
```

## Mã nguồn ngoài
- **picorv32**: `YosysHQ/picorv32` commit **`ef203c2b0a3fb793280f5114941416c425c5b461`**
  (2026-09-07, "Merge pull request #296 from YosysHQ/krys/archiving").
  File: `rtl/picorv32/picorv32.v`, 94.657 byte,
  sha256 `0836050971b3c6cdd28ac3b1e5719a67fb645161912bef1e472e63995ceb0622`.
  Tham số dùng ở F5 (đã đối chiếu README của picorv32 tại chính commit đó):
  `ENABLE_COUNTERS=1, ENABLE_COUNTERS64=1, ENABLE_REGS_16_31=1, ENABLE_REGS_DUALPORT=1,
  BARREL_SHIFTER=1, COMPRESSED_ISA=0, ENABLE_MUL=0, ENABLE_FAST_MUL=1, ENABLE_DIV=1,
  ENABLE_IRQ=0, ENABLE_PCPI=0, PROGADDR_RESET=0x00000000, STACKADDR=0x00010000`.
  README xác nhận: nếu đặt cả ENABLE_MUL và ENABLE_FAST_MUL thì ENABLE_MUL bị bỏ qua;
  các lõi PCPI nội bộ (mul/div) hoạt động không cần ENABLE_PCPI.

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
