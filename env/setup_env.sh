#!/bin/sh
# Môi trường công cụ cho dự án TinyML RISC-V / Tang Nano 20K (macOS x86_64).
# Dùng:  source env/setup_env.sh
# Ghi chú: file này chỉ export PATH, không cài gì. Phiên bản xem env/VERSIONS.md.

TNROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export TNROOT

# 1) OSS CAD Suite: yosys, nextpnr-himbaechel, gowin_pack (apycula), openFPGALoader, verilator, iverilog
OSSCAD="$HOME/tools/oss-cad-suite"
if [ -d "$OSSCAD/bin" ]; then
  export PATH="$OSSCAD/bin:$PATH"
else
  echo "CẢNH BÁO: không thấy $OSSCAD/bin" >&2
fi

# 2) Toolchain RISC-V (xPack GNU RISC-V Embedded GCC)
RVGCC="$HOME/tools/xpack-riscv-none-elf-gcc-15.2.0-1"
if [ -d "$RVGCC/bin" ]; then
  export PATH="$RVGCC/bin:$PATH"
else
  echo "CẢNH BÁO: không thấy $RVGCC/bin" >&2
fi

# 3) Python venv của dự án (numpy, pyserial)
if [ -d "$TNROOT/.venv/bin" ]; then
  export PATH="$TNROOT/.venv/bin:$PATH"
  export VIRTUAL_ENV="$TNROOT/.venv"
else
  echo "CẢNH BÁO: không thấy $TNROOT/.venv — chạy: python3 -m venv .venv" >&2
fi

# 4) Thông số dùng chung cho luồng Gowin / Tang Nano 20K
export TN20K_DEVICE="GW2AR-LV18QN88C8/I7"   # chuỗi --device của nextpnr-himbaechel
export TN20K_FAMILY="GW2A-18C"              # --vopt family= và gowin_pack -d
export TN20K_BOARD="tangnano20k"            # openFPGALoader -b
export TN20K_FREQ="27"                      # MHz, thạch anh trên kit
export TN20K_CST="$TNROOT/hw/tangnano20k.cst"

echo "Môi trường TN20K đã nạp. yosys=$(command -v yosys) riscv-gcc=$(command -v riscv-none-elf-gcc)"
