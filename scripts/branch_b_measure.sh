#!/bin/sh
# Đo toàn bộ nhánh B trong MỘT lượt liên tục, ngay sau khi cắm lại cáp USB.
#
# Lý do có script này: cổng UART của kit chết sau khoảng mười mấy phút không dùng
# (phần JTAG vẫn tốt — `--detect` vẫn nhận chip). Mỗi lần chết phải rút/cắm cáp,
# nên mọi phép đo phải gom vào một lượt, không xen việc tổng hợp bitstream.
#
# Trước và sau mỗi phép đo đều chạy ĐỐI CHỨNG bằng thiết kế tối giản top_min:
# nếu đối chứng im thì đường đo đã chết và SỐ ĐO KHÔNG CÓ GIÁ TRỊ — bài học ở B3,
# nơi tôi sửa thiết kế bốn lần trên một đường đo đã hỏng.
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
    if [ "$n" -ge 2 ]; then echo "ĐỐI CHỨNG ĐẠT ($1): thấy $n lần 'MIN'"; return 0
    else echo "ĐỐI CHỨNG KHÔNG ĐẠT ($1): đường UART đã chết — mọi số đo sau mốc này VÔ GIÁ TRỊ"; return 1
    fi
}

control "trước khi đo" || exit 1

for spec in "bv0 1" "bv1 1" "bv0r 0" "bv1r 0"; do
    v=$(echo "$spec" | cut -d' ' -f1)
    fa=$(echo "$spec" | cut -d' ' -f2)
    [ -f "$v/top.fs" ] || { echo "$v: chưa có bitstream, bỏ qua"; continue; }
    echo "########## $v (FAST_ADDR=$fa) ##########"
    make load-$v >/dev/null 2>&1 && echo "nạp OK"
    make check-$v FAST_ADDR=$fa 2>&1 | grep -E 'M1S_PASS|M1S_FAIL|ĐẠT:|chưa đủ|SRC_HASH' || true
    control "sau $v" || { echo "DỪNG: đường đo chết trong lúc đo $v"; exit 1; }
done

echo
echo "===== xong, đường đo còn tốt ở thời điểm kết thúc ====="
