#!/bin/sh

# RVT_LD / RVT_WORDS / RVT_STACK: cho phép chạy bộ kiểm trên cấu hình RAM 32 KB của
# bước S7 (bộ nhớ hai cổng). Mặc định y nguyên hành vi cũ: 64 KB, 16384 từ.
RVT_LD=${RVT_LD:-link_test.ld}
RVT_WORDS=${RVT_WORDS:-16384}
RVT_STACK=${RVT_STACK:-0x00010000}
# Dựng và chạy bộ riscv-tests (rv32ui-p + rv32um-p) trên một lõi.
#
#   scripts/riscv_tests.sh <thư mục làm việc> <đường dẫn Vsoc>
#
# Mỗi bài kiểm là một chương trình riêng, nạp vào firmware.hex rồi chạy mô phỏng.
# ĐẠT = mô phỏng in ra dòng "<tên>..OK" VÀ dòng "DONE"; mọi trường hợp khác là KHÔNG ĐẠT
# (ERROR do RVTEST_FAIL, trap do ebreak, hoặc quá hạn chu kỳ).
set -e
WORK=${1:?thiếu thư mục làm việc}
VSOC=${2:?thiếu đường dẫn Vsoc}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
T=$ROOT/rtl/mycore/tests
RT=$T/riscv-tests
CROSS=riscv-none-elf-
MAXC=${MAXC:-2000000}

mkdir -p "$WORK"
WORK=$(cd "$WORK" && pwd)
VSOC=$(cd "$(dirname "$VSOC")" && pwd)/$(basename "$VSOC")

n_pass=0; n_fail=0; failed=""
n_xpass=0; n_xfail=0; xinfo=""
for suite in rv32ui rv32um; do
    for src in "$RT"/isa/$suite/*.S; do
        name=$(basename "$src" .S)
        # Hai bài nằm NGOÀI RV32IM nên tính riêng, không vào điểm chính:
        #   ma_data  — cần hỗ trợ truy cập lệch địa chỉ (RV32IM không bắt buộc)
        #   fence_i  — cần phần mở rộng Zifencei
        extra=0
        case "$name" in
            ma_data|fence_i) extra=1 ;;
        esac
        rm -f "$WORK/firmware.hex" "$WORK/t.elf" "$WORK/t.bin"
        if ! "${CROSS}gcc" -march=rv32im_zifencei -mabi=ilp32 -nostdlib -nostartfiles -fno-pic -mno-relax \
             -I "$T" -I "$RT/isa/macros/scalar" -I "$RT/env" \
             -DTEST_FUNC_NAME=mytest -DTEST_FUNC_RET=mytest_ret \
             -DTEST_FUNC_TXT="\"$suite-p-$name\"" \
             -T "$T/$RVT_LD" -Wl,--no-warn-rwx-segments -DSTACK_TOP=$RVT_STACK \
             -o "$WORK/t.elf" "$T/start_test.S" "$src" 2> "$WORK/$name.cc.log"; then
            echo "$suite-p-$name KHÔNG DỊCH ĐƯỢC (xem $name.cc.log)"
            n_fail=$((n_fail+1)); failed="$failed $suite-p-$name(dịch)"; continue
        fi
        "${CROSS}objcopy" -O binary "$WORK/t.elf" "$WORK/t.bin"
        python3 "$ROOT/scripts/bin2hex.py" "$WORK/t.bin" "$WORK/firmware.hex" --words $RVT_WORDS > /dev/null
        ( cd "$WORK" && "$VSOC" --stop-on "DONE" --max-cycles $MAXC > "$name.log" 2> "$name.err" ) || true
        if grep -q "^$suite-p-$name\.\.OK" "$WORK/$name.log" && grep -q "^DONE" "$WORK/$name.log"; then
            if [ $extra -eq 1 ]; then
                echo "$suite-p-$name ĐẠT (ngoài RV32IM)"; n_xpass=$((n_xpass+1)); xinfo="$xinfo $name=ĐẠT"
            else
                echo "$suite-p-$name ĐẠT"; n_pass=$((n_pass+1))
            fi
        else
            why=$(grep -m1 -E "SIM_TRAP|SIM_TIMEOUT" "$WORK/$name.err" || true)
            out=$(tr -d '\r' < "$WORK/$name.log" | tr '\n' ' ')
            if [ $extra -eq 1 ]; then
                echo "$suite-p-$name KHÔNG ĐẠT (ngoài RV32IM) [$why] ra: $out"
                n_xfail=$((n_xfail+1)); xinfo="$xinfo $name=KHÔNG"
            else
                echo "$suite-p-$name KHÔNG ĐẠT  [$why] ra: $out"
                n_fail=$((n_fail+1)); failed="$failed $suite-p-$name"
            fi
        fi
    done
done
echo
echo "RV32IM: ĐẠT $n_pass · KHÔNG ĐẠT $n_fail"
echo "ngoài RV32IM (ma_data, fence_i): ĐẠT $n_xpass · KHÔNG ĐẠT $n_xfail ·$xinfo"
[ -n "$failed" ] && echo "bài không đạt:$failed"
[ "$n_fail" -eq 0 ] && echo "RISCV_TESTS_PASS n=$n_pass ngoai=$n_xpass/$((n_xpass+n_xfail))" \
                    || echo "RISCV_TESTS_FAIL dat=$n_pass khong_dat=$n_fail"
exit 0
