#!/bin/sh
# Đo nhánh B. Chịu được việc đường UART chết giữa đường: tiến độ TÍCH LUỸ, không mất.
#
# Bối cảnh: cổng UART của kit chết sau vài phép đo hoặc sau mười mấy phút không dùng
# (phần JTAG vẫn tốt). Chỉ rút/cắm lại cáp mới khôi phục. Vì vậy script này:
#
#  1. KHÔNG BAO GIỜ ghi đè file CSV. Trước mỗi phép đo, chỉ xoá các dòng CỦA CHÍNH
#     biến thể đó rồi ghi nối. Chạy một phần vẫn giữ nguyên số đã đo trước đó.
#     (Bản trước ghi đè ở biến thể đầu tiên và đã làm mất số đo hai lần.)
#  2. Chỉ chạy ĐỐI CHỨNG ở đầu lượt và sau một phép đo THẤT BẠI. Một phép đo thành
#     công đã tự chứng minh đường đo còn sống (CRC khớp golden + kit = Verilator),
#     nên đối chứng sau mỗi lần thành công chỉ làm tăng gấp đôi số lần nạp JTEG —
#     mà chính hoạt động JTAG có vẻ liên quan đến việc UART chết.
#  3. Bỏ qua biến thể đã có đủ 10 dòng trong CSV, trừ khi đặt FORCE=1.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT/rtl/mycore"
PORT=${PORT:-/dev/cu.usbserial-20250303171}
PY="$ROOT/.venv/bin/python"
CSV="$ROOT/results/branch_b/m1s_b.csv"

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
    [ "$n" -ge 2 ] && { echo "  [đối chứng ĐẠT: $n lần MIN]"; return 0; }
    echo "  [đối chứng KHÔNG ĐẠT — đường UART đã chết; cần rút/cắm lại cáp USB]"
    return 1
}

have() {  # đã có đủ 10 dòng cho biến thể $1 chưa?
    [ -f "$CSV" ] || return 1
    [ "$(awk -F, -v v="$1" 'NR>1 && $1==v' "$CSV" | wc -l | tr -d ' ')" = "10" ]
}

drop() {  # xoá các dòng của biến thể $1 (để ghi lại sạch)
    [ -f "$CSV" ] || return 0
    "$PY" - "$CSV" "$1" <<'PYEOF'
import csv, sys
path, var = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(path)))
if not rows: sys.exit()
keep = [r for r in rows if r['bien_the'] != var]
with open(path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(keep)
PYEOF
}

control || exit 1

#       dir : FAST_ADDR : WITH_DOT4 : nhãn kit báo      (quan trọng nhất lên trước)
LIST="bv1dc:1:1:A-V1+DOT4+C1
bv1d:1:1:A-V1+DOT4
bv2:1:1:A-V2
bv0:1:0:A-V0
bv1:1:0:A-V1
bv0r:0:0:A-V0
bv1r:0:0:A-V1"

n_ok=0; n_skip=0
for row in $LIST; do
    v=$(echo "$row" | cut -d: -f1); fa=$(echo "$row" | cut -d: -f2)
    d4=$(echo "$row" | cut -d: -f3); lbl=$(echo "$row" | cut -d: -f4)
    [ -f "$v/top.fs" ] || { echo "$v: chưa có bitstream, bỏ qua"; continue; }
    if [ "${FORCE:-0}" != "1" ] && have "$v"; then
        echo "$v: đã có đủ 10 dòng trong CSV, bỏ qua (FORCE=1 để đo lại)"
        n_skip=$((n_skip+1)); continue
    fi
    echo "########## $v  (FAST_ADDR=$fa WITH_DOT4=$d4)  nhãn kit: $lbl ##########"
    openFPGALoader -b tangnano20k "$v/top.fs" >/dev/null 2>&1 && echo "  nạp OK"
    drop "$v"
    out=$(make check-$v FAST_ADDR=$fa WITH_DOT4=$d4 CSV_APPEND="--append" 2>&1 || true)
    echo "$out" | grep -E 'M1S_PASS|M1S_FAIL|ĐẠT:|chưa đủ|SRC_HASH' || true
    if echo "$out" | grep -q 'M1S_PASS'; then
        n_ok=$((n_ok+1))
    else
        drop "$v"              # không đạt thì KHÔNG để lại dòng nào trong CSV
        echo "  $v KHÔNG ĐẠT — phân loại nguyên nhân bằng đối chứng:"
        control || { echo "DỪNG: đường đo chết. Rút/cắm lại cáp rồi chạy lại script —"; \
                     echo "      các biến thể đã đo xong sẽ được bỏ qua, tiến độ không mất."; exit 1; }
        echo "  (đối chứng ĐẠT => đường đo tốt, nên $v thực sự KHÔNG ĐẠT)"
    fi
done

echo
echo "===== đo xong $n_ok biến thể trong lượt này, bỏ qua $n_skip đã có ====="
"$PY" "$ROOT/scripts/branch_b_table.py" || true
