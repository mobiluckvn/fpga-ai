#!/bin/sh
# Đo toàn bộ nhánh B trong MỘT lượt liên tục, ngay sau khi cắm lại cáp USB.
#
# Vì sao phải một lượt: cổng UART của kit chết sau khoảng mười mấy phút không dùng
# (phần JTAG vẫn tốt — `--detect` vẫn nhận chip); đảo DTR/RTS hay đổi baud không
# khôi phục được, chỉ rút/cắm lại cáp. Nên mọi bitstream phải dựng SẴN trước.
#
# Trước và sau MỖI phép đo đều chạy ĐỐI CHỨNG bằng thiết kế tối giản `top_min`
# (chỉ bộ đếm + uart_tx, không lõi, không RAM 64 KB). Nếu đối chứng im thì đường đo
# đã chết và SỐ ĐO KHÔNG CÓ GIÁ TRỊ — bài học cổng B3, nơi tôi sửa thiết kế bốn lần
# trên một đường đo đã hỏng.
#
# Thứ tự đo: biến thể quan trọng nhất trước, để nếu đường đo chết giữa đường thì
# vẫn có số đáng giá nhất.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT/rtl/mycore"
PORT=${PORT:-/dev/cu.usbserial-20250303171}
PY="$ROOT/.venv/bin/python"

control() {
    openFPGALoader -b tangnano20k min/top.fs >/dev/null 2>&1
    n=$("$PY" - <<PYEOF
import serial, time
try:
    with serial.Serial("$PORT", 115200, timeout=0.5) as s:
        time.sleep(0.4); s.reset_input_buffer()
        t = time.time() + 2.5; b = b""
        while time.time() < t: b += s.read(8192)
    print(b.count(b"MIN"))
except Exception:
    print(0)
PYEOF
)
    if [ "$n" -ge 2 ]; then echo "  [đối chứng ĐẠT $1: $n lần MIN]"; return 0
    else echo "  [đối chứng KHÔNG ĐẠT $1 — đường UART chết, số đo sau mốc này VÔ GIÁ TRỊ]"; return 1
    fi
}

control "khởi đầu" || { echo "DỪNG: cần rút/cắm lại cáp USB"; exit 1; }

#       dir    FAST_ADDR WITH_DOT4 nhãn-kit-báo
# ĐO ĐỦ CẢ BẢY trong một lượt. Lý do: biến thể ĐẦU TIÊN ghi CSV mới (không --append),
# nên nếu chỉ đo một phần thì các dòng đã đo trước đó bị XOÁ — lỗi này đã xảy ra một
# lần và làm mất số đo bv0/bv1. Thứ tự đặt biến thể quan trọng nhất lên trước.
LIST="bv1dc:1:1:A-V1+DOT4+C1
bv1d:1:1:A-V1+DOT4
bv2:1:1:A-V2
bv0:1:0:A-V0
bv1:1:0:A-V1
bv0r:0:0:A-V0
bv1r:0:0:A-V1"

first=1
for row in $LIST; do
    v=$(echo "$row" | cut -d: -f1)
    fa=$(echo "$row" | cut -d: -f2)
    d4=$(echo "$row" | cut -d: -f3)
    lbl=$(echo "$row" | cut -d: -f4)
    [ -f "$v/top.fs" ] || { echo "$v: chưa có bitstream, bỏ qua"; continue; }
    echo "########## $v  (FAST_ADDR=$fa WITH_DOT4=$d4)  nhãn kit: $lbl ##########"
    openFPGALoader -b tangnano20k "$v/top.fs" >/dev/null 2>&1 && echo "  nạp OK"
    if [ $first -eq 1 ]; then APP=""; first=0; else APP="--append"; fi
    make check-$v FAST_ADDR=$fa WITH_DOT4=$d4 CSV_APPEND="$APP" 2>&1 \
        | grep -E 'M1S_PASS|M1S_FAIL|ĐẠT:|chưa đủ|SRC_HASH' || true
    control "sau $v" || { echo "DỪNG: đường đo chết trong lúc đo $v"; exit 1; }
done

echo
echo "===== XONG, đường đo còn tốt ở thời điểm kết thúc ====="
"$ROOT/.venv/bin/python" "$ROOT/scripts/branch_b_table.py" || true
