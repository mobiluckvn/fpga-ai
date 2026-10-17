#!/bin/sh
# Lưu TOÀN BỘ vật phẩm của một cổng kiểm chứng vào results/feasibility/<GATE>/
#
# Dùng:  scripts/archive_gate.sh <GATE> <BUILD_DIR> [file/thư mục khác cần lưu ...]
# Ví dụ: scripts/archive_gate.sh F1 feasibility/F1_blinky/build
#        scripts/archive_gate.sh F0 -            (dùng "-" khi cổng không có thư mục build)
#
# Sinh ra:
#   results/feasibility/<GATE>/artifacts/   — bản sao mọi file trong BUILD_DIR và các file thêm
#   results/feasibility/<GATE>/MANIFEST.md  — ngày, commit, phiên bản công cụ, SHA256 + kích thước
#
# Mục đích: báo cáo phải truy nguyên được. Mỗi con số trong FEASIBILITY_REPORT.md phải
# đối chiếu được về một file ở đây (quy tắc 3 trong CLAUDE.md).
set -e

GATE="$1"
BUILD="$2"
if [ -z "$GATE" ] || [ -z "$BUILD" ]; then
    echo "Dùng: $0 <GATE> <BUILD_DIR> [file khác ...]" >&2
    exit 2
fi
shift 2

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST="$ROOT/results/feasibility/$GATE"
ART="$DEST/artifacts"
mkdir -p "$ART"

# --- sao chép vật phẩm ---
if [ "$BUILD" = "-" ]; then
    :   # cổng không có thư mục build (vd. F0: chỉ có log)
elif [ -d "$BUILD" ]; then
    find "$BUILD" -type f -exec cp -f {} "$ART"/ \;
else
    echo "CẢNH BÁO: không thấy thư mục build '$BUILD'" >&2
fi
for extra in "$@"; do
    if [ -e "$extra" ]; then
        cp -Rf "$extra" "$ART"/
    else
        echo "CẢNH BÁO: không thấy '$extra'" >&2
    fi
done

# --- manifest ---
MAN="$DEST/MANIFEST.md"
{
    echo "# Vật phẩm cổng $GATE"
    echo
    echo "- Ngày lưu: \`$(date '+%Y-%m-%d %H:%M:%S %z')\`"
    echo "- Git commit lúc lưu: \`$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo 'chưa commit')\`"
    echo "- Thư mục build nguồn: \`$BUILD\`"
    echo "- Máy: \`$(uname -srm)\` · macOS \`$(sw_vers -productVersion 2>/dev/null)\`"
    echo
    echo "## Phiên bản công cụ lúc tạo vật phẩm"
    echo '```'
    echo "oss-cad-suite  $(cat "$HOME/tools/oss-cad-suite/VERSION" 2>/dev/null || echo '?')"
    command -v yosys              >/dev/null 2>&1 && yosys -V 2>/dev/null | head -1
    command -v nextpnr-himbaechel >/dev/null 2>&1 && nextpnr-himbaechel --version 2>&1 | head -1
    command -v openFPGALoader     >/dev/null 2>&1 && openFPGALoader -V 2>&1 | head -1
    command -v verilator          >/dev/null 2>&1 && verilator --version 2>&1 | head -1
    command -v iverilog           >/dev/null 2>&1 && iverilog -V 2>&1 | head -1
    command -v riscv-none-elf-gcc >/dev/null 2>&1 && riscv-none-elf-gcc --version 2>&1 | head -1
    echo '```'
    echo
    echo "## File đã lưu (SHA256, kích thước byte)"
    echo
    echo "| File | Byte | SHA256 |"
    echo "|---|---:|---|"
    for f in $(cd "$DEST" && find . -type f ! -name MANIFEST.md ! -name .gitkeep | sed 's|^\./||' | sort); do
        sz=$(wc -c < "$DEST/$f" | tr -d ' ')
        sha=$(shasum -a 256 "$DEST/$f" | cut -d' ' -f1)
        echo "| \`$f\` | $sz | \`$sha\` |"
    done
} > "$MAN"

echo "Đã lưu vật phẩm $GATE vào $DEST"
echo "  $(find "$DEST" -type f | wc -l | tr -d ' ') file, tổng $(du -sh "$DEST" | cut -f1)"
echo "  manifest: results/feasibility/$GATE/MANIFEST.md"
